"""Helpers for handling stale DM callbacks after a game has ended.

Telegram keeps buttons on past messages forever, so a player who went
AFK or simply scrolled up can tap a night-action / vote button hours
after the game wrapped up. Without this guard those handlers blow up
trying to mutate a no-longer-existing state.

`is_stale_for_user` is the cheap precondition check; `notify_and_drop`
shows a translated alert and deletes the obsolete message in one shot.
"""

from __future__ import annotations

import contextlib

from aiogram.types import CallbackQuery

from app.core.state import GameState, Phase
from app.db.models import User
from app.services import game_service
from app.services.i18n_service import Translator


async def resolve_active_state(user: User) -> GameState | None:
    """Return the live state for the user's *current* game, or None.

    None means the user has no active game registered (`active_game_id`
    is null) OR the Redis state for that game has expired. Either way the
    DM button the caller is processing is from a finished game.
    """
    if user.active_game_id is None:
        return None
    from app.db.models import Game

    db_game = await Game.get_or_none(id=user.active_game_id)
    if db_game is None:
        return None
    return await game_service.load_state(db_game.group_id)


async def notify_and_drop(
    query: CallbackQuery,
    _plain: Translator,
    *,
    alert_key: str = "dm-stale-game-alert",
) -> None:
    """Tell the user the game is over and remove the stale DM message.

    Both the alert and the delete are best-effort — Telegram will
    sometimes return 'message to delete not found' if it has already
    expired (48h limit) or 'query is too old' for very stale callbacks.
    Neither matters for correctness; we just want to be quiet.
    """
    with contextlib.suppress(Exception):
        await query.answer(_plain(alert_key), show_alert=True)
    if query.message is not None:
        with contextlib.suppress(Exception):
            await query.message.delete()  # type: ignore[union-attr]


def is_stale_for_phase(state: GameState | None, expected: Phase) -> bool:
    """Convenience wrapper: state missing or no longer in the expected phase."""
    return state is None or state.phase != expected
