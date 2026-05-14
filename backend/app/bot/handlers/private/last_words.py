"""Private chat: capture mafia chat messages + last words from dead players.

Single combined handler — aiogram 3 doesn't fall through between routers,
so both responsibilities must share one entry point. Resolution order on
each non-command private text:

  1. If the sender is an alive mafia member during NIGHT, relay it to
     teammates (mafia chat) and stop.
  2. Otherwise, if the sender has a pending "last words" slot, broadcast
     their message to the group and consume the slot.
  3. Otherwise, no-op.
"""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import Message
from loguru import logger

from app.db.models import User
from app.services import game_service
from app.services.last_words import (
    broadcast_last_words,
    consume_last_words,
    is_last_words_pending,
)
from app.services.mafia_chat import relay_mafia_message

router = Router(name="private_last_words")
router.message.filter(F.chat.type == "private", F.text)


@router.message()
async def capture_private_text(message: Message, user: User, bot: Bot) -> None:
    if message.text is None or message.text.startswith("/"):
        return

    # 1. Mafia chat relay (night only, mafia members only).
    relayed = await relay_mafia_message(bot, user.id, message.text)
    if relayed:
        return

    # 2. Last words capture (dead players within their timeout window).
    group_id = await is_last_words_pending(user.id)
    if group_id is None:
        return

    state = await game_service.load_state(group_id)
    if state is None:
        await consume_last_words(user.id)
        return

    await broadcast_last_words(bot, state, user.id, message.text)
    await consume_last_words(user.id)
    await game_service.save_state(state)
    logger.info(f"Last words from user {user.id} broadcast to group {group_id}")
