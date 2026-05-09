"""Private chat: receive role night action target picks via inline callbacks."""

from __future__ import annotations

import contextlib

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.core.state import NightAction, Phase
from app.db.models import User
from app.services import game_service
from app.services.i18n_service import Translator
from app.services.role_actions import role_action_type

router = Router(name="private_role_actions")
router.callback_query.filter(F.data.startswith("night:"))


@router.callback_query(F.data.startswith("night:"))
async def handle_night_pick(query: CallbackQuery, user: User, _: Translator) -> None:
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
            with contextlib.suppress(Exception):
                await query.message.edit_text(_("night-skipped-confirm"))
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
        with contextlib.suppress(Exception):
            await query.message.edit_text(_("night-action-confirmed", target=target.first_name))


async def _find_state_by_game_id(game_id) -> object | None:
    """Find live state for a game by game UUID — scan group_ids.

    For MVP simplicity: load Game from DB to get group_id.
    """
    from app.db.models import Game

    db_game = await Game.get_or_none(id=game_id)
    if db_game is None:
        return None
    return await game_service.load_state(db_game.group_id)
