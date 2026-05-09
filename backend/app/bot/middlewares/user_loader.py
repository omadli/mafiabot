"""Middleware: load User from DB and inject into handler data."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from app.db.models import User, UserInventory


class UserLoaderMiddleware(BaseMiddleware):
    """Yuklovchi: get-or-create User va UserInventory."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        tg_user = self._extract_user(event)
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        user, _ = await User.get_or_create(
            id=tg_user.id,
            defaults={
                "first_name": tg_user.first_name or "",
                "last_name": tg_user.last_name,
                "username": tg_user.username,
                "language_code": tg_user.language_code or "uz",
            },
        )
        # Update mutable fields
        if (
            user.username != tg_user.username
            or user.first_name != (tg_user.first_name or "")
            or user.last_name != tg_user.last_name
        ):
            user.username = tg_user.username
            user.first_name = tg_user.first_name or ""
            user.last_name = tg_user.last_name
            await user.save(update_fields=["username", "first_name", "last_name"])

        # Ensure inventory exists
        await UserInventory.get_or_create(user=user)

        data["user"] = user
        return await handler(event, data)

    @staticmethod
    def _extract_user(update: Update) -> Any:
        for source in (
            update.message,
            update.callback_query,
            update.inline_query,
            update.chat_member,
            update.my_chat_member,
            update.chat_join_request,
            update.pre_checkout_query,
        ):
            if source is not None and source.from_user is not None:
                return source.from_user
        return None
