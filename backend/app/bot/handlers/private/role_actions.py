"""Private chat: receive role night action target picks via inline callbacks."""

from __future__ import annotations

import asyncio
import contextlib

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from app.config import settings as app_settings
from app.core.state import GameState, NightAction, Phase, Team
from app.db.models import Group, User
from app.services import game_service
from app.services.i18n_service import Translator, get_translator
from app.services.role_actions import role_action_type

router = Router(name="private_role_actions")
router.callback_query.filter(F.data.startswith("night:"))


async def _back_to_group_kb(state: GameState, _: Translator) -> InlineKeyboardMarkup:
    """Build a single-button keyboard pointing the user back at the group."""
    group = await Group.get_or_none(id=state.group_id)
    url = (
        group.invite_link
        if group and group.invite_link
        else f"https://t.me/{app_settings.bot_username}"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("btn-back-to-group"), url=url)]]
    )


@router.callback_query(F.data.startswith("night:detchoose:"))
async def handle_detective_chooser(
    query: CallbackQuery, user: User, _: Translator, bot: Bot
) -> None:
    """Detective picked 'check' or 'kill' — edit the chooser DM to show
    the target keyboard. The actual target selection is then handled by
    handle_night_pick via callback `night:detective:<action>:<target>`."""
    if query.data is None or query.message is None:
        await query.answer()
        return
    parts = query.data.split(":")
    if len(parts) != 3 or parts[2] not in ("check", "kill"):
        await query.answer("Invalid", show_alert=True)
        return
    action_kind = parts[2]

    if user.active_game_id is None:
        await query.answer(_("night-not-in-active-game"), show_alert=True)
        return
    state = await _find_state_by_game_id(user.active_game_id)
    if state is None or state.phase != Phase.NIGHT:
        await query.answer(_("night-not-in-night-phase"), show_alert=True)
        return

    actor = state.get_player(user.id)
    if actor is None or not actor.alive or actor.role != "detective":
        await query.answer(_("night-cannot-act"), show_alert=True)
        return

    from app.services.role_actions import send_detective_target_keyboard

    locale = state.settings.get("language", "uz")
    kb = await send_detective_target_keyboard(bot, state, actor, action_kind, locale)
    if kb is None:
        await query.answer(_("night-no-targets"), show_alert=True)
        return

    prompt = _(
        "night-prompt-detective-target-list-check"
        if action_kind == "check"
        else "night-prompt-detective-target-list-kill"
    )
    with contextlib.suppress(Exception):
        await query.message.edit_text(prompt, reply_markup=kb, parse_mode="HTML")
    await query.answer()


@router.callback_query(F.data.startswith("night:"))
async def handle_night_pick(query: CallbackQuery, user: User, _: Translator, bot: Bot) -> None:
    if query.data is None:
        await query.answer()
        return

    parts = query.data.split(":")
    # night:<role>:<target_id>  OR  night:detective:<action>:<target_id>
    try:
        if parts[1] == "detective" and len(parts) == 4:
            role_code = "detective"
            action_kind = parts[2]  # check | kill
            target_id = int(parts[3])
        else:
            role_code = parts[1]
            target_id = int(parts[2])
            action_kind = role_action_type(role_code)
    except (IndexError, ValueError):
        await query.answer("Invalid", show_alert=True)
        return

    # Find which group this user is in
    if user.active_game_id is None:
        await query.answer(_("night-not-in-active-game"), show_alert=True)
        return

    state = await _find_state_by_game_id(user.active_game_id)
    if state is None or state.phase != Phase.NIGHT:
        await query.answer(_("night-not-in-night-phase"), show_alert=True)
        return

    actor = state.get_player(user.id)
    if actor is None or not actor.alive or actor.role != role_code:
        await query.answer(_("night-cannot-act"), show_alert=True)
        return

    # Skip
    if target_id == 0:
        state.current_actions.pop(user.id, None)
        await game_service.save_state(state)
        await query.answer(_("night-skipped"), show_alert=False)
        if query.message:
            back_kb = await _back_to_group_kb(state, _)
            with contextlib.suppress(Exception):
                await query.message.edit_text(_("night-skipped-confirm"), reply_markup=back_kb)
        return

    # Validate target
    target = state.get_player(target_id)
    if target is None or not target.alive:
        await query.answer(_("night-target-invalid"), show_alert=True)
        return

    # Record action
    action = NightAction(
        actor_id=user.id,
        role=role_code,
        action_type=action_kind,
        target_id=target_id,
    )
    state.current_actions[user.id] = action
    await game_service.save_state(state)

    await query.answer(
        _("night-action-recorded", target=target.first_name),
        show_alert=False,
    )
    if query.message:
        back_kb = await _back_to_group_kb(state, _)
        with contextlib.suppress(Exception):
            await query.message.edit_text(
                _("night-action-confirmed", target=target.first_name),
                reply_markup=back_kb,
                parse_mode="HTML",
            )

    # Broadcast to other alive mafia teammates if actor is on the mafia team.
    # Lets the team coordinate / see each other's picks during night.
    if actor.team == Team.MAFIA:
        await _broadcast_to_mafia(bot, state, actor, target, action_kind)

    # Atmospheric per-role broadcast to the GROUP (idempotent per round).
    # Each role posts at most once per night — Mafia + Don share the
    # "Don tanladi" message so the team is treated as one. Detective has
    # two flavors depending on action_type.
    await _broadcast_role_atmosphere(bot, state, actor, action_kind)


_BROADCAST_KEY_OVERRIDES: dict[tuple[str, str], str] = {
    # Detective branches:
    ("detective", "check"): "night-action-msg-detective-check",
    ("detective", "kill"): "night-action-msg-detective-shoot",
    # Whole mafia team shares the "Don is choosing" line:
    ("mafia", "kill"): "night-action-msg-don",
    ("don", "kill"): "night-action-msg-don",
}


def _atmosphere_key(role_code: str, action_kind: str) -> str:
    return _BROADCAST_KEY_OVERRIDES.get((role_code, action_kind), f"night-action-msg-{role_code}")


async def _broadcast_role_atmosphere(
    bot: Bot,
    state: GameState,
    actor: object,  # PlayerState
    action_kind: str,
) -> None:
    """Post the role's atmospheric line to the group, at most once per round."""
    role_code = getattr(actor, "role", None)
    if not role_code:
        return

    key = _atmosphere_key(role_code, action_kind)
    round_log = state.current_round()
    posted: set[str] = set(round_log.__dict__.setdefault("broadcast_atmosphere_keys", []))
    if key in posted:
        return
    posted.add(key)
    round_log.__dict__["broadcast_atmosphere_keys"] = list(posted)
    await game_service.save_state(state)

    locale = state.settings.get("language", "uz")
    t = get_translator(locale)
    text = t(key)
    # Fluent returns the key itself when missing — bail silently in that case.
    if text == key:
        return
    with contextlib.suppress(Exception):
        await bot.send_message(state.chat_id, text)


async def _broadcast_to_mafia(
    bot: Bot,
    state: GameState,
    actor,
    target,
    action_kind: str,
) -> None:
    """Notify other alive mafia members of one member's night pick."""
    locale = state.settings.get("language", "uz")
    t = get_translator(locale)
    actor_role_label = t(f"role-{actor.role}")

    text = t(
        "mafia-team-pick-broadcast",
        role=actor_role_label,
        actor=actor.first_name,
        target=target.first_name,
        action=action_kind,
    )

    async def _dm(uid: int) -> None:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
        except TelegramForbiddenError:
            pass
        except Exception as e:
            logger.debug(f"Mafia pick broadcast DM to {uid} failed: {e}")

    targets = [
        p.user_id
        for p in state.alive_players()
        if p.team == Team.MAFIA and p.user_id != actor.user_id
    ]
    if not targets:
        return
    await asyncio.gather(*(_dm(uid) for uid in targets), return_exceptions=True)


async def _find_state_by_game_id(game_id) -> object | None:
    """Find live state for a game by game UUID — scan group_ids.

    For MVP simplicity: load Game from DB to get group_id.
    """
    from app.db.models import Game

    db_game = await Game.get_or_none(id=game_id)
    if db_game is None:
        return None
    return await game_service.load_state(db_game.group_id)
