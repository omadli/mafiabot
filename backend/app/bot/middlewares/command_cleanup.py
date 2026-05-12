"""Middleware: auto-delete /command messages in groups after the handler runs.

Reference parity (@MafiaAzBot): the underlined slash-command text in group
chats invites spam — newer members tap it and the chat fills with the same
command. Once the bot has processed the command we delete the user's
message (best-effort; needs delete_messages admin right).

Scope:
- Group / supergroup chats only (private chats are left alone — users see
  their own history there).
- Messages that look like a slash-command (text starts with '/' or contains
  bot-command entity).
- Runs AFTER the handler, so the handler still has access to message data.
"""

from __future__ import annotations

import contextlib
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class CommandCleanupMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        result = await handler(event, data)

        if (
            isinstance(event, Message)
            and event.chat.type in ("group", "supergroup")
            and _is_command(event)
        ):
            with contextlib.suppress(Exception):
                await event.delete()

        return result


def _is_command(message: Message) -> bool:
    text = message.text or message.caption or ""
    if text.startswith("/"):
        return True
    for ent in message.entities or message.caption_entities or []:
        if ent.type == "bot_command" and ent.offset == 0:
            return True
    return False
