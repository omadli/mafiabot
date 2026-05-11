"""Game-start announcement helpers.

Called on the first NIGHT phase transition (round_num == 1):
- Broadcasts "🎭 O'yin boshlandi!" in the group with an inline button
  "🎭 Sizning rolingiz" that opens an alert showing the caller's role.
- DMs each alive player privately with:
    "Siz - 🤵🏼 Mafiya siz!
    <short role description>"
  plus a "🔙 Guruhga o'tish" URL button (uses group's invite_link if set,
  otherwise a deep link via the bot).
"""

from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from app.config import settings
from app.core.state import GameState
from app.db.models import Group
from app.services.i18n_service import get_translator


async def announce_game_started(bot: Bot, state: GameState) -> None:
    """Group post + per-player DM."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    # --- 1. Group message with "Sizning rolingiz" button ---
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("btn-show-my-role"),
                    callback_data=f"game:show-role:{state.id}",
                )
            ]
        ]
    )
    try:
        await bot.send_message(
            state.chat_id,
            _("game-started-announcement"),
            reply_markup=kb,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"announce_game_started: group send failed: {e}")

    # --- 2. Per-player DM ---
    group = await Group.get_or_none(id=state.group_id)
    invite_link = (
        group.invite_link
        if group and group.invite_link
        else f"https://t.me/{settings.bot_username}"
    )

    back_btn = InlineKeyboardButton(text=_("btn-back-to-group"), url=invite_link)
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])

    async def _send_dm(player_id: int, role: str) -> None:
        try:
            t = get_translator(locale)
            role_label = t(f"role-{role}")
            desc = t(f"role-desc-{role}")
            text = t("dm-your-role", role=role_label, description=desc)
            await bot.send_message(player_id, text, reply_markup=back_kb, parse_mode="HTML")
        except TelegramForbiddenError:
            logger.debug(f"Cannot DM player {player_id} (forbidden)")
        except Exception as e:
            logger.debug(f"Role DM to {player_id} failed: {e}")

    await asyncio.gather(
        *[_send_dm(p.user_id, p.role) for p in state.players if p.role],
        return_exceptions=True,
    )
