"""Filter: only super admins (Telegram user IDs from settings) pass."""

from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.config import settings


class IsSuperAdmin(BaseFilter):
    """Pass only if message.from_user.id is in SUPER_ADMIN_TELEGRAM_IDS."""

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        return message.from_user.id in settings.super_admin_ids
