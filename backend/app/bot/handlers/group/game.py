"""Group game commands: /game, /leave, /stop, /extend, /vote.

Game lifecycle wired to Redis state via game_service.
"""

from __future__ import annotations

import contextlib

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    Message,
)
from loguru import logger

from app.bot.handlers.shared.registration import (
    build_registration_keyboard,
    format_registration_text,
)
from app.config import settings
from app.core.phases.manager import PhaseManager
from app.core.state import Phase, Vote
from app.db.models import Group, User
from app.services import game_service
from app.services.i18n_service import Translator
from app.services.messaging import (
    broadcast_game_end,
    broadcast_night_results,
    broadcast_phase_change,
)

router = Router(name="group_game")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


@router.message(Command("game", "newgame"))
async def cmd_game(
    message: Message, user: User, _: Translator, command: CommandObject, bot: Bot
) -> None:
    """Boshlash: ro'yxatdan o'tish fazasi."""
    chat_id = message.chat.id
    group = await Group.get_or_none(id=chat_id).prefetch_related("settings")
    if group is None or not group.onboarding_completed:
        await message.answer(_("game-onboarding-required"))
        return

    # Permission check
    perms = group.settings.permissions if group.settings else {}
    who_can = perms.get("who_can_register", "all")
    if who_can == "admins":
        member = await bot.get_chat_member(chat_id, user.id)
        if member.status not in ("creator", "administrator"):
            await message.answer(_("error-only-admins"))
            return

    # Bounty parsing: /game 50
    bounty_per_winner: int | None = None
    if command.args:
        try:
            bounty_per_winner = int(command.args.strip().split()[0])
            if bounty_per_winner < 1:
                bounty_per_winner = None
        except (ValueError, IndexError):
            pass

    # Bounty escrow check + actual escrow transfer
    if bounty_per_winner is not None:
        required = bounty_per_winner * 10
        if user.diamonds < required:
            await message.answer(
                _("game-bounty-insufficient", required=required, have=user.diamonds)
            )
            return
        try:
            from app.services.giveaway_service import GiveawayError, escrow_bounty

            await escrow_bounty(user, bounty_per_winner)
        except GiveawayError as e:
            await message.answer(_(str(e)))
            return

    try:
        state = await game_service.create_game(group, user, bounty_per_winner)
    except game_service.GameError as e:
        await message.answer(_(str(e)))
        return

    # Send registration message
    text = format_registration_text(state, _)
    keyboard = build_registration_keyboard(state, settings.bot_username, _)
    sent = await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)

    # Save message_id for later edits
    state.registration_message_id = sent.message_id
    await game_service.save_state(state)

    # Auto-pin
    if group.settings and group.settings.display.get("auto_pin_registration", True):
        try:
            await bot.pin_chat_message(chat_id, sent.message_id, disable_notification=True)
        except Exception as e:
            logger.warning(f"Could not pin: {e}")

    # Start phase manager
    PhaseManager.start_for(
        bot, group_id=chat_id, on_phase_change=lambda s: _on_phase_change(bot, s)
    )


@router.message(Command("leave"))
async def cmd_leave(message: Message, user: User, _: Translator, bot: Bot) -> None:
    """O'yindan chiqib ketish."""
    state = await game_service.load_state(message.chat.id)
    if state is None or state.get_player(user.id) is None:
        await message.answer(_("leave-not-in-game"))
        return

    permissions = state.settings.get("permissions", {})
    if not permissions.get("allow_leave", True):
        await message.answer(_("leave-not-allowed"))
        return

    player = state.get_player(user.id)
    if player is None:
        await message.answer(_("leave-not-in-game"))
        return

    # Registration phase: just unregister, no penalty
    if state.phase == Phase.WAITING:
        await game_service.unregister_player(state, user.id)
        await message.answer(_("unjoin-success", name=user.first_name))
        await _refresh_registration_message(bot, state, _)
        return

    # In-game leave: mark dead with LEFT reason
    from app.core.state import DeathReason

    if not player.alive:
        await message.answer(_("leave-already-dead"))
        return

    player.alive = False
    player.died_at_round = state.round_num
    player.died_at_phase = state.phase
    player.died_reason = DeathReason.LEFT
    await game_service.save_state(state)
    await game_service.set_user_active_game(user.id, None)

    # ELO/XP penalty (Bosqich 2 — to'liq qo'llanadi)
    leave_msg_template = state.settings.get("messages", {}).get("leave_message", "")
    from app.services.messaging import player_mention

    mention = player_mention(user.id, user.first_name)
    if leave_msg_template:
        text = leave_msg_template.replace("{mention}", mention)
    else:
        text = _("leave-broadcast", mention=mention)
    await message.answer(text)


@router.message(Command("stop"))
async def cmd_stop(message: Message, user: User, _: Translator, bot: Bot) -> None:
    """O'yinni bekor qilish."""
    state = await game_service.load_state(message.chat.id)
    if state is None:
        await message.answer(_("stop-no-game"))
        return

    perms = state.settings.get("permissions", {})
    who_can = perms.get("who_can_stop", "admins")
    if who_can == "none":
        await message.answer(_("stop-not-allowed"))
        return
    if who_can == "admins":
        member = await bot.get_chat_member(message.chat.id, user.id)
        if member.status not in ("creator", "administrator"):
            await message.answer(_("error-only-admins"))
            return

    PhaseManager.cancel_for(message.chat.id)
    await game_service.cancel_game(state, reason="admin-stopped")
    await message.answer(_("stop-success"))


@router.message(Command("extend"))
async def cmd_extend(message: Message, user: User, _: Translator, command: CommandObject) -> None:
    """Ro'yxatdan o'tish vaqtini uzaytirish."""
    state = await game_service.load_state(message.chat.id)
    if state is None or state.phase != Phase.WAITING:
        await message.answer(_("extend-not-in-registration"))
        return

    extra = 30
    if command.args:
        with contextlib.suppress(ValueError):
            extra = max(10, min(120, int(command.args.strip())))

    if state.phase_ends_at is not None:
        state.phase_ends_at += extra
    await game_service.save_state(state)
    await message.answer(_("extend-success", seconds=extra))


@router.message(Command("vote"))
async def cmd_vote(message: Message, user: User, _: Translator, command: CommandObject) -> None:
    """Kunduzgi ovoz: /vote @user yoki reply."""
    state = await game_service.load_state(message.chat.id)
    if state is None or state.phase != Phase.VOTING:
        await message.answer(_("vote-not-in-voting"))
        return

    voter = state.get_player(user.id)
    if voter is None or not voter.alive:
        await message.answer(_("vote-not-alive"))
        return

    target_id: int | None = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id

    if target_id is None and command.args:
        # Try parse @username
        text = command.args.strip()
        if text.startswith("@"):
            uname = text[1:]
            target_player = next((p for p in state.alive_players() if p.username == uname), None)
            if target_player is not None:
                target_id = target_player.user_id

    if target_id is None:
        await message.answer(_("vote-target-required"))
        return

    target = state.get_player(target_id)
    if target is None or not target.alive:
        await message.answer(_("vote-target-invalid"))
        return

    weight = 2 if voter.role == "mayor" else 1
    state.current_votes[user.id] = Vote(voter_id=user.id, target_id=target_id, weight=weight)
    await game_service.save_state(state)

    show_anon = state.settings.get("display", {}).get("anonymous_voting", False)
    if show_anon:
        await message.answer(_("vote-recorded-anon"))
    else:
        from app.services.messaging import player_mention

        await message.answer(
            _(
                "vote-recorded",
                voter=player_mention(voter.user_id, voter.first_name),
                target=player_mention(target.user_id, target.first_name),
            )
        )


# === Inline join callback ===


@router.callback_query(F.data.startswith("game:join:"))
async def callback_join(query: CallbackQuery, user: User, _: Translator, bot: Bot) -> None:
    """Inline tugma orqali registratsiya — alternativ deeplink uchun."""
    if query.data is None or query.message is None:
        await query.answer()
        return
    try:
        group_id = int(query.data.split(":")[2])
    except (IndexError, ValueError):
        await query.answer("Invalid", show_alert=True)
        return

    # Just redirect user to bot via deeplink (same flow as deeplink)
    deeplink = f"https://t.me/{settings.bot_username}?start=join_{group_id}"
    await query.answer(_("click-to-join-private"), url=deeplink)


# === Helpers ===


async def _refresh_registration_message(bot: Bot, state, _: Translator) -> None:
    """Update the registration message with new player list."""
    if state.registration_message_id is None:
        return
    text = format_registration_text(state, _)
    keyboard = build_registration_keyboard(state, settings.bot_username, _)
    try:
        await bot.edit_message_text(
            text,
            chat_id=state.chat_id,
            message_id=state.registration_message_id,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.debug(f"Could not edit registration message: {e}")


async def _on_phase_change(bot: Bot, state) -> None:
    """Hook called by PhaseManager after each phase transition."""
    from app.bot.handlers.group.voting import announce_hanging_confirm, announce_voting
    from app.services.role_actions import send_night_prompts

    if state.phase == Phase.NIGHT:
        await broadcast_phase_change(bot, state)
        await send_night_prompts(bot, state)
        # Open mafia private chat
        from app.services.mafia_chat import announce_mafia_chat_open

        await announce_mafia_chat_open(bot, state)
    elif state.phase == Phase.DAY:
        await _broadcast_results_from_log(bot, state)
        await broadcast_phase_change(bot, state)
    elif state.phase == Phase.VOTING:
        await broadcast_phase_change(bot, state)
        await announce_voting(bot, state)
    elif state.phase == Phase.HANGING_CONFIRM:
        # Get pending hang target from round log
        target_id = state.current_round().__dict__.get("pending_hang_target")
        if target_id:
            await announce_hanging_confirm(bot, state, target_id)
    elif state.phase in (Phase.FINISHED, Phase.CANCELLED):
        await broadcast_game_end(bot, state)


async def _broadcast_results_from_log(bot: Bot, state) -> None:
    """Reconstruct night outcome from current round log and broadcast."""
    from app.core.actions import NightOutcome

    round_log = state.current_round() if state.rounds else None
    if round_log is None:
        return
    outcome = NightOutcome(
        deaths=round_log.night_deaths,
        death_reasons={},
        detective_results=[],
        doctor_results=[],
        sleeping=set(),
    )
    await broadcast_night_results(bot, state, outcome)
