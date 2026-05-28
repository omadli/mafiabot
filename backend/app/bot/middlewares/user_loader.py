"""Middleware: load User from DB and inject into handler data.

Sandbox awareness: fake user_ids (negative, allocated by
`app.core.sandbox_ids`) NEVER touch the DB. Their data lives in Redis
(see `transcript_store.set_fake_users`) and we hydrate an unsaved
in-memory `User` instance for the handler to consume. This is the only
load-bearing patch needed in the engine for the sandbox feature: the
DB CHECK constraint (`users.id > 0`) would otherwise loudly reject
any escaped negative ID, but we go a step further and never call
`get_or_create` for them at all.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from loguru import logger

from app.core.sandbox_ids import is_sandbox_user_id
from app.db.models import User, UserInventory
from app.services import transcript_store


class UserLoaderMiddleware(BaseMiddleware):
    """Yuklovchi: get-or-create User va UserInventory.

    Sandbox fake users are loaded from Redis instead — no DB writes.
    """

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

        # --- Sandbox short-circuit -----------------------------------------
        # Negative user_id ⇒ this is a synthetic update from
        # `sandbox_service.inject_callback`. Build an unsaved User and
        # bypass every DB path.
        if is_sandbox_user_id(tg_user.id):
            fake = await transcript_store.lookup_user(tg_user.id)
            if fake is None:
                # Defensive — sandbox TTL'd or middleware fired for an ID
                # outside any active session. Drop silently rather than
                # corrupt the DB with a get_or_create.
                logger.warning(
                    f"UserLoader: sandbox user {tg_user.id} has no Redis entry; dropping update"
                )
                return None
            user = self._build_sandbox_user(fake)
            data["user"] = user
            data["sandbox_id"] = fake.get("sandbox_id")
            return await handler(event, data)

        # --- Real users (DB path) ------------------------------------------
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
    def _build_sandbox_user(fake: dict[str, Any]) -> User:
        """Construct an in-memory `User` that mimics a saved row.

        We DO NOT call `.save()` — the DB CHECK constraint
        (`users.id > 0`) would reject the negative id. Downstream code
        only reads `.id`, `.first_name`, `.username`, `.language_code`,
        and `.active_game_id`; everything else is harmless to default.
        """
        user = User(
            id=fake["user_id"],
            first_name=fake.get("first_name") or "Player",
            last_name=None,
            username=fake.get("username"),
            language_code=fake.get("language_code") or "uz",
        )
        # `_saved_in_db` is Tortoise's "this row exists in DB" flag. Setting
        # it True tricks `.save(update_fields=...)` into doing an UPDATE
        # rather than an INSERT — but since sandbox guards skip every
        # save call upstream, this is belt-and-braces.
        user._saved_in_db = True  # type: ignore[attr-defined]
        return user

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
