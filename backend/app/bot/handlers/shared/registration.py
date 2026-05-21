"""Registration message helpers — text + inline keyboard."""

from __future__ import annotations

import time

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.state import GameState
from app.services.i18n_service import Translator
from app.services.messaging import player_mention


def format_registration_text(
    state: GameState, _: Translator, _plain: Translator | None = None
) -> str:
    """Build the group registration message text.

    When `phase_ends_at` is None (`/extend` flipped the registration to
    indefinite), the timer line is omitted — printing `00:00` there is
    misleading because the deadline has been removed, not reached.
    """
    if state.players:
        player_list = "\n".join(
            f"{p.join_order}. {player_mention(p.user_id, p.first_name)}" for p in state.players
        )
    else:
        player_list = _("registration-no-players-yet")

    if state.phase_ends_at is None:
        body = _(
            "registration-message-indefinite",
            count=len(state.players),
            players=player_list,
        )
    else:
        remaining = max(0, state.phase_ends_at - int(time.time()))
        minutes, seconds = divmod(remaining, 60)
        timer = f"{minutes:02d}:{seconds:02d}"
        body = _(
            "registration-message",
            timer=timer,
            count=len(state.players),
            players=player_list,
        )

    bounty_line = ""
    if state.bounty_per_winner:
        bounty_line = "\n" + _(
            "registration-bounty",
            per_winner=state.bounty_per_winner,
            pool=state.bounty_pool,
        )

    return body + bounty_line


def build_registration_keyboard(
    state: GameState,
    bot_username: str,
    _: Translator,
    _plain: Translator | None = None,
) -> InlineKeyboardMarkup:
    """Inline keyboard for registration — deeplink to bot."""
    deeplink = f"https://t.me/{bot_username}?start=join_{state.group_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_plain("btn-join-game"), url=deeplink)],
        ]
    )
