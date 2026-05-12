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
from app.core.state import Phase
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
    """Boshlash: ro'yxatdan o'tish fazasi.

    Existing WAITING game → re-broadcast the registration post (delete old,
    post fresh). Existing in-game (NIGHT/DAY/VOTING) → reject.
    """
    chat_id = message.chat.id
    group = await Group.get_or_none(id=chat_id).prefetch_related("settings")
    if group is None or not group.onboarding_completed:
        await message.answer(_("game-onboarding-required"))
        return

    # If a registration is already open, just refresh it instead of
    # erroring out with "game already running".
    existing = await game_service.load_state(chat_id)
    if existing is not None and existing.phase == Phase.WAITING:
        await _re_announce_registration(bot, existing, _)
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
    from app.services.messaging import player_mention, role_emoji_name

    mention = player_mention(user.id, user.first_name)
    show_role_on_death = state.settings.get("display", {}).get("show_role_on_death", True)

    if leave_msg_template:
        text = leave_msg_template.replace("{mention}", mention)
    elif show_role_on_death and player.role:
        # Reference parity (@MafiaAzBot): role oshkor qilinadi
        role_label = role_emoji_name(player.role, state.settings.get("language", "uz"))
        role_parts = role_label.split(" ", 1)
        role_emoji = role_parts[0] if role_parts else "❓"
        role_name = role_parts[1] if len(role_parts) > 1 else player.role
        text = _(
            "leave-broadcast-with-role",
            mention=mention,
            role_emoji=role_emoji,
            role_name=role_name,
        )
    else:
        text = _("leave-broadcast", mention=mention)
    await message.answer(text, parse_mode="HTML")


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
async def cmd_extend(message: Message, user: User, _: Translator) -> None:
    """Ro'yxatdan o'tish vaqtini cheksiz uzaytirish (timeout o'chiriladi).

    `/start` bosilguncha o'yin avtomatik boshlanmaydi.
    """
    state = await game_service.load_state(message.chat.id)
    if state is None or state.phase != Phase.WAITING:
        await message.answer(_("extend-not-in-registration"))
        return

    state.phase_ends_at = None  # disable auto-timeout
    await game_service.save_state(state)
    await message.answer(_("extend-indefinite"))


# === Inline join callback ===


@router.callback_query(F.data.startswith("game:show-role:"))
async def callback_show_my_role(query: CallbackQuery, user: User, _: Translator) -> None:
    """Show the caller their assigned role as an alert.

    Triggered by the "🎭 Sizning rolingiz" button on the game-started message.
    Non-players get an explicit "you are not in this game" alert.
    """
    if query.data is None or query.message is None:
        await query.answer()
        return

    state = await game_service.load_state(query.message.chat.id)
    if state is None:
        await query.answer(_("show-role-no-game"), show_alert=True)
        return

    player = state.get_player(user.id)
    if player is None:
        await query.answer(_("show-role-not-in-game"), show_alert=True)
        return

    role_label = _(f"role-{player.role}")
    role_desc = _(f"role-desc-{player.role}")
    text = _("show-role-alert", role=role_label, description=role_desc)
    # Telegram caps callback answer text at ~200 chars
    if len(text) > 195:
        text = text[:192] + "..."
    await query.answer(text, show_alert=True)


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


# === /start group command (registration starter / launcher) ===


@router.message(Command("start", "go", "begin"))
async def cmd_start(
    message: Message, user: User, _: Translator, command: CommandObject, bot: Bot
) -> None:
    """Group `/start` command — context-aware:

    Active registration (WAITING phase):
      - Admin OR creator → launch the game now (if enough players)
      - Other user → re-broadcast registration message at bottom of chat
        (deletes the previous one + unpins, then pins the fresh one)

    No active registration:
      - Treat as `/game` and start a new registration.
    """
    chat_id = message.chat.id

    state = await game_service.load_state(chat_id)

    # === Case A: Active registration ===
    if state is not None and state.phase == Phase.WAITING:
        # Is the caller authorized to launch the game?
        is_admin = False
        try:
            member = await bot.get_chat_member(chat_id, user.id)
            is_admin = member.status in ("creator", "administrator")
        except Exception as e:
            logger.debug(f"/start get_chat_member failed: {e}")

        is_creator = state.creator_user_id == user.id

        if is_admin or is_creator:
            # Launch the game now
            min_players = state.settings.get("gameplay", {}).get("min_players", 4)
            if len(state.players) < min_players:
                await message.reply(_("game-not-enough-players"))
                return
            try:
                await game_service.start_game(state)
            except game_service.GameError as e:
                await message.reply(_(str(e)))
                return
            await game_service.save_state(state)

            # Clean up the stale registration message — the upcoming
            # "game started" announcement makes it obsolete.
            await _delete_registration_message(bot, state)

            # Manually fire the NIGHT phase-change hook. The phase manager
            # was sleeping on phase_ends_at=None (post-/extend) and will not
            # invoke on_phase_change for this NIGHT transition. Without
            # this call, players never receive role DMs / night prompts.
            try:
                await _on_phase_change(bot, state)
            except Exception as e:
                logger.exception(f"on_phase_change after /start failed: {e}")
            return

        # Non-admin, non-creator → just re-announce
        await _re_announce_registration(bot, state, _)
        return

    # === Case B: No active registration ===
    # Permission check (same logic as /game)
    group = await Group.get_or_none(id=chat_id).prefetch_related("settings")
    if group is None or not group.onboarding_completed:
        await message.answer(_("game-onboarding-required"))
        return

    perms = group.settings.permissions if group.settings else {}
    who_can = perms.get("who_can_register", "all")
    if who_can == "admins":
        try:
            member = await bot.get_chat_member(chat_id, user.id)
            if member.status not in ("creator", "administrator"):
                await message.reply(_("error-only-admins"))
                return
        except Exception:
            await message.reply(_("error-only-admins"))
            return

    # Defer to /game handler (creates state + announces)
    await cmd_game(message, user, _, command, bot)


async def _delete_registration_message(bot: Bot, state) -> None:
    """Unpin + delete the stale registration message (best-effort)."""
    if state.registration_message_id is None:
        return
    with contextlib.suppress(Exception):
        await bot.unpin_chat_message(
            chat_id=state.chat_id, message_id=state.registration_message_id
        )
    with contextlib.suppress(Exception):
        await bot.delete_message(chat_id=state.chat_id, message_id=state.registration_message_id)
    state.registration_message_id = None
    await game_service.save_state(state)


async def _re_announce_registration(bot: Bot, state, _: Translator) -> None:
    """Re-send the registration message — delete the old one, unpin, post fresh, pin again.

    Keeps the existing player list visible at the bottom of the chat (handy
    when registration scrolled out of view after a busy stretch).
    """
    chat_id = state.chat_id
    old_msg_id = state.registration_message_id

    # Unpin + delete the old message (best-effort)
    if old_msg_id is not None:
        with contextlib.suppress(Exception):
            await bot.unpin_chat_message(chat_id=chat_id, message_id=old_msg_id)
        with contextlib.suppress(Exception):
            await bot.delete_message(chat_id=chat_id, message_id=old_msg_id)

    # Send fresh registration message
    text = format_registration_text(state, _)
    keyboard = build_registration_keyboard(state, settings.bot_username, _)
    sent = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )
    state.registration_message_id = sent.message_id
    await game_service.save_state(state)

    # Pin if group settings allow
    pin_enabled = state.settings.get("display", {}).get("auto_pin_registration", True)
    if pin_enabled:
        with contextlib.suppress(Exception):
            await bot.pin_chat_message(chat_id, sent.message_id, disable_notification=True)


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
        # On the FIRST night, announce game start + role-reveal button + DM roles
        if state.round_num == 1:
            from app.services.game_start_announce import announce_game_started

            await announce_game_started(bot, state)

        # Broadcast previous round's hanging result before next night begins
        await _broadcast_hanging_result(bot, state)
        await broadcast_phase_change(bot, state)
        await send_night_prompts(bot, state)
        # Open mafia private chat
        from app.services.mafia_chat import announce_mafia_chat_open

        await announce_mafia_chat_open(bot, state)
    elif state.phase == Phase.DAY:
        await _broadcast_results_from_log(bot, state)
        await broadcast_phase_change(bot, state)
        # Send alive players summary (numbered list + team breakdown)
        from app.services.alive_summary import format_alive_summary

        try:
            summary = format_alive_summary(state)
            await bot.send_message(state.group_id, summary, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to send alive summary: {e}")
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


async def _broadcast_hanging_result(bot: Bot, state) -> None:
    """Broadcast the hanging verdict in a single combined message and delete
    the now-stale 👍/👎 confirm message from the chat.

    Looks at the most recent round prior to current round_num (the
    just-finished day).
    """
    from app.services.i18n_service import get_translator
    from app.services.messaging import player_mention

    if state.round_num <= 1 or not state.rounds:
        return  # first round — no previous voting yet

    prev_round = None
    for r in state.rounds:
        if r.round_num == state.round_num - 1:
            prev_round = r
            break
    if prev_round is None:
        return

    extras = prev_round.__dict__
    yes_total = extras.get("hang_yes_total")
    no_total = extras.get("hang_no_total")
    if yes_total is None and no_total is None:
        return  # no hanging confirm happened

    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    # Remove the live-tally 👍/👎 confirm message — it's now stale.
    confirm_msg_id = extras.get("hanging_confirm_msg_id")
    if confirm_msg_id:
        with contextlib.suppress(Exception):
            await bot.delete_message(chat_id=state.group_id, message_id=confirm_msg_id)

    # Cancelled (yes <= no, or no votes) — single message.
    if extras.get("hang_cancelled"):
        try:
            await bot.send_message(
                state.group_id,
                _("hanging-cancelled", yes=yes_total or 0, no=no_total or 0),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.debug(f"Hanging cancel broadcast failed: {e}")
        return

    # Successful hanging — single combined "tally + osildi" message.
    if not prev_round.hanged:
        return

    hanged_role = extras.get("hanged_role", "")
    hanged_name = extras.get("hanged_name", "")
    show_role = state.settings.get("display", {}).get("show_role_on_death", True)
    mention = player_mention(prev_round.hanged, hanged_name)
    try:
        if show_role and hanged_role:
            from app.services.alive_summary import ROLE_DISPLAY

            emoji, role_name = ROLE_DISPLAY.get(hanged_role, ("", hanged_role))
            msg = _(
                "hanging-combined-with-role",
                yes=yes_total or 0,
                no=no_total or 0,
                mention=mention,
                role_emoji=emoji,
                role=role_name,
            )
        else:
            msg = _(
                "hanging-combined",
                yes=yes_total or 0,
                no=no_total or 0,
                mention=mention,
            )
        await bot.send_message(state.group_id, msg, parse_mode="HTML")
    except Exception as e:
        logger.debug(f"Hanging combined broadcast failed: {e}")


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
