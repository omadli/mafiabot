"""Private chat handler: capture last words from dead players."""

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

router = Router(name="private_last_words")
router.message.filter(F.chat.type == "private", F.text)


@router.message()
async def capture_last_words(message: Message, user: User, bot: Bot) -> None:
    """If user has pending last-words slot, capture their first message and broadcast."""
    if message.text is None or message.text.startswith("/"):
        return

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
