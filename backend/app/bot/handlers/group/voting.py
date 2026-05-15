"""Voting UI — moved out of group chat, runs in player DMs.

Flow:
  1. `announce_voting()` posts a SHORT group message with a single "Ovoz berish"
     URL button that deeplinks every voter into a private chat with the bot.
  2. In parallel, the bot DMs each alive player a per-target keyboard
     (one row per candidate, excluding self). Teammates are marked with
     a role emoji so the player can avoid friendly fire.
  3. The vote callback (`vote:cast:<id>`) is now received in the private
     chat. The handler edits the DM with a confirmation and (if voting is
     not anonymous) broadcasts the choice back to the group.

Hanging-confirm phase remains in the group: the 👍 / 👎 buttons show LIVE
counts that update each time someone reacts. Dead players, non-players,
and double-tappers receive comedic rumor-style alerts instead of silent
no-ops.
"""

from __future__ import annotations

import asyncio
import contextlib

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from loguru import logger

from app.config import settings as app_settings
from app.core.state import GameState, Phase, PlayerState, Team, Vote
from app.db.models import User
from app.services import game_service
from app.services.i18n_service import Translator, get_translator
from app.services.messaging import player_mention, role_emoji_name

router = Router(name="group_voting")


# === Keyboards ===


def _team_marker(voter: PlayerState, target: PlayerState) -> str:
    """Return a leading emoji for `target` from `voter`'s perspective.

    Mafia voters see their teammates marked with 🤵, Detective/Sergeant
    see their partner marked with 🕵. Everyone else gets no marker.
    """
    if voter.team == Team.MAFIA and target.team == Team.MAFIA:
        return "🤵 "
    if voter.role in ("detective", "sergeant") and target.role in ("detective", "sergeant"):
        return "🕵 "
    return ""


def build_dm_voting_keyboard(
    state: GameState, voter: PlayerState, _: Translator
) -> InlineKeyboardMarkup:
    """Per-voter keyboard: one row per alive target except self."""
    rows: list[list[InlineKeyboardButton]] = []
    for target in state.alive_players():
        if target.user_id == voter.user_id:
            continue
        marker = _team_marker(voter, target)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{marker}#{target.join_order} {target.first_name}",
                    callback_data=f"vote:cast:{target.user_id}",
                )
            ]
        )
    if state.settings.get("gameplay", {}).get("allow_skip_day_vote", True):
        rows.append([InlineKeyboardButton(text=_("vote-skip-button"), callback_data="vote:cast:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _confirm_button_label(prefix_emoji: str, count: int) -> str:
    """Label like '👍 3' or '👎' when count is 0."""
    return f"{prefix_emoji} {count}" if count > 0 else prefix_emoji


def build_confirm_keyboard(
    target_user_id: int, yes_count: int = 0, no_count: int = 0
) -> InlineKeyboardMarkup:
    """👍/👎 keyboard with live counts on the button labels."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_confirm_button_label("👍", yes_count),
                    callback_data=f"hangconfirm:yes:{target_user_id}",
                ),
                InlineKeyboardButton(
                    text=_confirm_button_label("👎", no_count),
                    callback_data=f"hangconfirm:no:{target_user_id}",
                ),
            ]
        ]
    )


def _safe_html(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# === Vote cast callback (received in private chat) ===


@router.callback_query(F.data.startswith("vote:cast:"))
async def callback_vote_cast(query: CallbackQuery, user: User, _: Translator, bot: Bot) -> None:
    if query.data is None:
        await query.answer()
        return
    try:
        target_id = int(query.data.split(":")[2])
    except (IndexError, ValueError):
        await query.answer("Invalid", show_alert=True)
        return

    # Resolve state via user.active_game_id (callback comes from private chat
    # now, so we cannot rely on query.message.chat.id).
    state = await _state_for_user(user)
    if state is None or state.phase != Phase.VOTING:
        await query.answer(_("vote-not-in-voting"), show_alert=True)
        return

    voter = state.get_player(user.id)
    if voter is None:
        await query.answer(_("vote-not-in-game-alert"), show_alert=True)
        return
    if not voter.alive:
        await query.answer(_("vote-dead-alert"), show_alert=True)
        return

    if target_id == user.id:
        await query.answer(_("vote-cannot-self"), show_alert=True)
        return

    target: PlayerState | None = None
    if target_id != 0:
        target = state.get_player(target_id)
        if target is None or not target.alive:
            await query.answer(_("vote-target-invalid"), show_alert=True)
            return

    # Already voted same target → friendly nudge, no state change
    prior = state.current_votes.get(user.id)
    if prior is not None and prior.target_id == target_id:
        await query.answer(_("vote-already-voted-alert"), show_alert=True)
        return

    # Mayor 2x weight; Aferist proxy support (records as the impersonated user)
    weight = 2 if voter.role == "mayor" else 1
    voter_id_for_record = user.id
    crook_proxy_victim_id: int | None = None
    if voter.role == "crook":
        proxy_target_id = voter.extra.get("proxy_target")
        if proxy_target_id is not None:
            proxy_target = state.get_player(proxy_target_id)
            if proxy_target is not None and proxy_target.alive:
                voter_id_for_record = proxy_target_id
                crook_proxy_victim_id = proxy_target_id
                weight = 2 if proxy_target.role == "mayor" else 1

    state.current_votes[user.id] = Vote(
        voter_id=voter_id_for_record, target_id=target_id, weight=weight
    )
    await game_service.save_state(state)

    if crook_proxy_victim_id is not None:
        with contextlib.suppress(Exception):
            await bot.send_message(crook_proxy_victim_id, _("crook-stole-vote-dm"))

    show_anon = state.settings.get("display", {}).get("anonymous_voting", False)
    display_voter = state.get_player(voter_id_for_record) or voter
    voter_mention = player_mention(display_voter.user_id, display_voter.first_name)
    if display_voter.role == "mayor":
        locale = state.settings.get("language", "uz")
        voter_display = f"{role_emoji_name(display_voter.role, locale)} {voter_mention}"
    else:
        voter_display = voter_mention

    # Confirmation toast + DM edit
    if target_id == 0:
        await query.answer(_("vote-skipped-toast"), show_alert=False)
        confirm_text = _("vote-skipped-confirm")
    else:
        assert target is not None  # mypy: validated above
        await query.answer(_("vote-recorded-toast", target=target.first_name), show_alert=False)
        confirm_text = _("vote-recorded-dm-confirm", target=_safe_html(target.first_name))

    if query.message is not None:
        back_kb = await _back_to_group_kb(state, _)
        with contextlib.suppress(Exception):
            await query.message.edit_text(confirm_text, reply_markup=back_kb, parse_mode="HTML")

    # Public broadcast (non-anonymous only)
    if not show_anon:
        try:
            if target_id == 0:
                await bot.send_message(
                    state.chat_id,
                    _("vote-broadcast-abstain", voter=voter_display),
                    parse_mode="HTML",
                )
            else:
                assert target is not None
                await bot.send_message(
                    state.chat_id,
                    _(
                        "vote-broadcast",
                        voter=voter_display,
                        target=player_mention(target.user_id, target.first_name),
                    ),
                    parse_mode="HTML",
                )
        except Exception as e:
            logger.debug(f"Vote broadcast failed: {e}")


# === Hanging confirm callback (group chat, 👍/👎 with live counts) ===


@router.callback_query(F.data.startswith("hangconfirm:"))
async def callback_hanging_confirm(
    query: CallbackQuery, user: User, _: Translator, bot: Bot
) -> None:
    if query.data is None or query.message is None:
        await query.answer()
        return
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer("Invalid", show_alert=True)
        return
    decision = parts[1]
    try:
        target_id = int(parts[2])
    except ValueError:
        await query.answer("Invalid", show_alert=True)
        return

    chat_id = query.message.chat.id
    state = await game_service.load_state(chat_id)
    if state is None or state.phase != Phase.HANGING_CONFIRM:
        await query.answer(_("hanging-confirm-expired"), show_alert=True)
        return

    voter = state.get_player(user.id)
    if voter is None:
        await query.answer(_("vote-not-in-game-alert"), show_alert=True)
        return
    if not voter.alive:
        await query.answer(_("vote-dead-alert"), show_alert=True)
        return

    # The person being hanged cannot vote in their own hanging confirm.
    if voter.user_id == target_id:
        await query.answer(_("hanging-confirm-cannot-self"), show_alert=True)
        return

    weight = 2 if voter.role == "mayor" else 1

    confirm_data: dict = state.current_round().extra.setdefault(
        "hanging_confirm",
        {"target_id": target_id, "yes": {}, "no": {}},
    )

    voter_key = str(user.id)
    if decision == "yes":
        if voter_key in confirm_data["yes"]:
            await query.answer(_("vote-already-voted-alert"), show_alert=True)
            return
        confirm_data["yes"][voter_key] = weight
        confirm_data["no"].pop(voter_key, None)
        toast = "👍"
    else:
        if voter_key in confirm_data["no"]:
            await query.answer(_("vote-already-voted-alert"), show_alert=True)
            return
        confirm_data["no"][voter_key] = weight
        confirm_data["yes"].pop(voter_key, None)
        toast = "👎"

    await game_service.save_state(state)
    await query.answer(toast, show_alert=False)

    # Live-update message with new counts
    yes_total = sum(confirm_data.get("yes", {}).values())
    no_total = sum(confirm_data.get("no", {}).values())
    target = state.get_player(target_id)
    if target is None:
        return
    new_kb = build_confirm_keyboard(target_id, yes_total, no_total)
    new_text = _(
        "hanging-confirm-prompt",
        target=player_mention(target_id, target.first_name),
    )
    with contextlib.suppress(Exception):
        await query.message.edit_text(new_text, reply_markup=new_kb, parse_mode="HTML")


# === Helpers called from PhaseManager hook ===


async def announce_voting(bot: Bot, state: GameState) -> None:
    """Voting fazasi boshlanganda:
    - Group: short prompt + "Ovoz berish" URL button (deeplinks into bot DM).
    - DM each alive player a per-target keyboard.
    """
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    timings = state.settings.get("timings", {})
    seconds = timings.get("hanging_vote", 45)

    bot_url = f"https://t.me/{app_settings.bot_username}"
    group_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("voting-go-button"), url=bot_url)]]
    )
    try:
        await bot.send_message(
            state.chat_id,
            _("voting-group-prompt-short", seconds=seconds),
            reply_markup=group_kb,
        )
    except Exception as e:
        logger.warning(f"Could not send voting group prompt: {e}")

    # Proactive per-player DMs
    async def _dm(player: PlayerState) -> None:
        try:
            kb = build_dm_voting_keyboard(state, player, _)
            await bot.send_message(
                player.user_id,
                _("voting-dm-prompt"),
                reply_markup=kb,
                parse_mode="HTML",
            )
        except TelegramForbiddenError:
            pass
        except Exception as e:
            logger.debug(f"Voting DM to {player.user_id} failed: {e}")

    await asyncio.gather(*(_dm(p) for p in state.alive_players()), return_exceptions=True)


async def announce_hanging_confirm(bot: Bot, state: GameState, target_id: int) -> None:
    """Eng ko'p ovoz olgan o'yinchi uchun 👍/👎 (live counts).

    Stores the sent message_id on the round log so it can be removed when
    the timer expires and the verdict is broadcast.
    """
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)
    target = state.get_player(target_id)
    if target is None:
        return

    keyboard = build_confirm_keyboard(target_id, 0, 0)
    text = _(
        "hanging-confirm-prompt",
        target=player_mention(target_id, target.first_name),
    )
    try:
        sent = await bot.send_message(state.chat_id, text, reply_markup=keyboard, parse_mode="HTML")
        state.current_round().extra["hanging_confirm_msg_id"] = sent.message_id
        await game_service.save_state(state)
    except Exception as e:
        logger.warning(f"Hanging confirm message failed: {e}")


# === Deeplink entry from group "Ovoz berish" button ===


async def send_vote_dm_for_deeplink(bot: Bot, user: User, state: GameState, _: Translator) -> str:
    """Called by /start vote_<group_id> deeplink handler. Returns an i18n
    key the caller can use to send an appropriate reply (or empty string
    when the DM keyboard was already pushed)."""
    if state.phase != Phase.VOTING:
        return "vote-not-in-voting"

    voter = state.get_player(user.id)
    if voter is None:
        return "vote-not-in-game-alert"
    if not voter.alive:
        return "vote-dead-alert"

    kb = build_dm_voting_keyboard(state, voter, _)
    with contextlib.suppress(Exception):
        await bot.send_message(user.id, _("voting-dm-prompt"), reply_markup=kb, parse_mode="HTML")
    return ""


# === Internal ===


async def _state_for_user(user: User) -> GameState | None:
    if user.active_game_id is None:
        return None
    from app.db.models import Game

    game = await Game.get_or_none(id=user.active_game_id)
    if game is None:
        return None
    return await game_service.load_state(game.group_id)


async def _back_to_group_kb(state: GameState, _: Translator) -> InlineKeyboardMarkup:
    from app.db.models import Group

    group = await Group.get_or_none(id=state.group_id)
    url = (
        group.invite_link
        if group and group.invite_link
        else f"https://t.me/{app_settings.bot_username}"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("btn-back-to-group"), url=url)]]
    )
