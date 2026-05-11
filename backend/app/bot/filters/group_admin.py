"""Filter: pass only if the message author is a group admin or creator."""

from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message
from loguru import logger


class IsGroupAdmin(BaseFilter):
    """Telegram chat administrator check.

    Used on group/supergroup messages. Calls `chat.get_member()` once per
    invocation — Telegram caches member status briefly, so this is cheap.

    Returns False for private chats (no group concept).
    """

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None or message.chat.type not in ("group", "supergroup"):
            return False
        try:
            member = await message.chat.get_member(message.from_user.id)
        except Exception as e:
            logger.debug(f"IsGroupAdmin get_member failed: {e}")
            return False
        return member.status in ("administrator", "creator")
