"""Registration message helpers — text + inline keyboard."""

from __future__ import annotations

import time

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.state import GameState
from app.services.i18n_service import Translator
from app.services.messaging import player_mention


def format_registration_text(state: GameState, _: Translator) -> str:
    """Build the group registration message text."""
    remaining = max(0, (state.phase_ends_at or 0) - int(time.time()))
    minutes, seconds = divmod(remaining, 60)
    timer = f"{minutes:02d}:{seconds:02d}"

    if state.players:
        player_list = "\n".join(
            f"{p.join_order}. {player_mention(p.user_id, p.first_name)}" for p in state.players
        )
    else:
        player_list = _("registration-no-players-yet")

    bounty_line = ""
    if state.bounty_per_winner:
        bounty_line = "\n" + _(
            "registration-bounty",
            per_winner=state.bounty_per_winner,
            pool=state.bounty_pool,
        )

    return (
        _(
            "registration-message",
            timer=timer,
            count=len(state.players),
            players=player_list,
        )
        + bounty_line
    )


def build_registration_keyboard(
    state: GameState, bot_username: str, _: Translator
) -> InlineKeyboardMarkup:
    """Inline keyboard for registration — deeplink to bot."""
    deeplink = f"https://t.me/{bot_username}?start=join_{state.group_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("btn-join-game"), url=deeplink)],
        ]
    )
