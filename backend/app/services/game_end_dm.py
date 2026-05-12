"""Per-player game-end DM — sends each participant a personal summary.

Called by `finish_game()` after `finalize_game_stats()` has written the
`GameResult` rows. Reads each row back to determine the player's outcome
and rewards, then DMs them with their role, win/loss, and XP / ELO /
dollar deltas. Includes a "Guruhga o'tish" button so the player can hop
back to the group chat.
"""

from __future__ import annotations

import asyncio
import contextlib

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from app.config import settings
from app.core.state import GameState
from app.db.models import GameResult, Group
from app.services.i18n_service import get_translator


async def send_per_player_game_end_dm(bot: Bot, state: GameState) -> None:
    """DM every participant their personal end-of-game summary."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    results = await GameResult.filter(game_id=state.id).all()
    if not results:
        return

    group = await Group.get_or_none(id=state.group_id)
    url = (
        group.invite_link
        if group and group.invite_link
        else f"https://t.me/{settings.bot_username}"
    )
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("btn-back-to-group"), url=url)]]
    )

    async def _send(result: GameResult) -> None:
        try:
            role_label = _(f"role-{result.role}")
            elo_sign = "+" if result.elo_change >= 0 else ""
            key = "game-end-dm-win" if result.won else "game-end-dm-loss"
            text = _(
                key,
                role=role_label,
                xp=result.xp_earned,
                elo_delta=f"{elo_sign}{result.elo_change}",
                dollars=result.dollars_earned,
            )
            await bot.send_message(result.user_id, text, reply_markup=back_kb, parse_mode="HTML")
        except TelegramForbiddenError:
            pass
        except Exception as e:
            logger.debug(f"Game-end DM to {result.user_id} failed: {e}")

    with contextlib.suppress(Exception):
        await asyncio.gather(*(_send(r) for r in results), return_exceptions=True)
