"""Flood throttle for group commands.

Per (user, chat) cooldown of COOLDOWN_SECONDS between any two commands.
Inside the window:
- 1st extra hit: silent drop.
- 2nd+ extra hits: drop + reply with a randomized comedic scold.

Single-process in-memory tracker (bot runs as one instance). Keys are
short-lived; the dict is opportunistically pruned on every call.
"""

from __future__ import annotations

import random
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from loguru import logger

COOLDOWN_SECONDS = 2.5
ALERT_AFTER_HITS = 2  # 1st extra = silent, 2nd+ extra = scold

ALERT_KEYS = (
    "flood-alert-1",
    "flood-alert-2",
    "flood-alert-3",
    "flood-alert-4",
)


def _is_command(msg: Message) -> bool:
    text = msg.text or msg.caption or ""
    if text.startswith(("/", "!")):
        return True
    return any(
        e.type == "bot_command" and e.offset == 0
        for e in (msg.entities or msg.caption_entities or [])
    )


class ThrottlingMiddleware(BaseMiddleware):
    """Rate-limit consecutive group commands from the same user."""

    def __init__(self) -> None:
        super().__init__()
        # (user_id, chat_id) -> (last_ts, hits_within_window)
        self._state: dict[tuple[int, int], tuple[float, int]] = {}

    def _prune(self, now: float) -> None:
        # Drop entries older than 30s to keep memory tidy.
        stale = [k for k, (ts, _) in self._state.items() if now - ts > 30.0]
        for k in stale:
            self._state.pop(k, None)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if (
            not isinstance(event, Message)
            or event.chat.type not in ("group", "supergroup")
            or event.from_user is None
            or not _is_command(event)
        ):
            return await handler(event, data)

        now = time.monotonic()
        key = (event.from_user.id, event.chat.id)
        last_ts, hits = self._state.get(key, (0.0, 0))

        if now - last_ts < COOLDOWN_SECONDS:
            hits += 1
            self._state[key] = (now, hits)
            if hits >= ALERT_AFTER_HITS:
                translator = data.get("_")
                if translator is not None:
                    try:
                        await event.reply(translator(random.choice(ALERT_KEYS)))
                    except Exception as e:
                        logger.debug(f"flood-alert send failed: {e}")
            return None

        self._state[key] = (now, 0)
        if len(self._state) > 256:
            self._prune(now)
        return await handler(event, data)
