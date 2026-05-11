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
