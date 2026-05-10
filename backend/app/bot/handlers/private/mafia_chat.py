"""Private chat: capture mafia text messages and relay during night."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import Message

from app.db.models import User
from app.services.mafia_chat import relay_mafia_message

router = Router(name="private_mafia_chat")
router.message.filter(F.chat.type == "private", F.text)


@router.message()
async def capture_mafia_chat(message: Message, user: User, bot: Bot) -> None:
    """Try to relay text as mafia chat. If not eligible, fall through silently."""
    if message.text is None or message.text.startswith("/"):
        return
    # Try mafia relay first; if not eligible, last_words handler will pick it up
    relayed = await relay_mafia_message(bot, user.id, message.text)
    if relayed:
        # Optional: echo back confirmation marker (skip for cleaner UX)
        return
