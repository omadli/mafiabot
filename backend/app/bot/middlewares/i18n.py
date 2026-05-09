"""Middleware: set up i18n locale and inject `_` translator function."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from app.db.models import Group, User
from app.services.i18n_service import get_translator


class I18nMiddleware(BaseMiddleware):
    """Lokal tilni aniqlaydi (User > Group > 'uz') va translator inject qiladi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        locale = "uz"  # default

        # 1. User-level (private chat)
        user: User | None = data.get("user")
        if user is not None and user.language_code:
            locale = user.language_code

        # 2. Group-level (overrides for group context)
        if isinstance(event, Update):
            chat = self._extract_chat(event)
            if chat is not None and chat.type in ("group", "supergroup"):
                group = await Group.get_or_none(id=chat.id).prefetch_related("settings")
                if group is not None and group.settings is not None:
                    locale = group.settings.language

        data["locale"] = locale
        data["_"] = get_translator(locale)
        return await handler(event, data)

    @staticmethod
    def _extract_chat(update: Update) -> Any:
        for source in (
            update.message,
            update.callback_query,
            update.chat_member,
            update.my_chat_member,
        ):
            if source is None:
                continue
            chat = getattr(source, "chat", None) or (
                getattr(source.message, "chat", None)
                if hasattr(source, "message") and source.message
                else None
            )
            if chat is not None:
                return chat
        return None
