"""WebSocket broker — broadcast game events to admin panel subscribers."""

from __future__ import annotations

import asyncio
import json
from typing import Any, ClassVar

from fastapi import WebSocket
from loguru import logger


class AdminBroker:
    """In-memory pub/sub for admin panel WebSocket subscribers."""

    _subscribers: ClassVar[set[WebSocket]] = set()
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    @classmethod
    async def subscribe(cls, ws: WebSocket) -> None:
        async with cls._lock:
            cls._subscribers.add(ws)
        logger.debug(f"Admin WS subscribed (total: {len(cls._subscribers)})")

    @classmethod
    async def unsubscribe(cls, ws: WebSocket) -> None:
        async with cls._lock:
            cls._subscribers.discard(ws)
        logger.debug(f"Admin WS unsubscribed (total: {len(cls._subscribers)})")

    @classmethod
    async def broadcast(cls, event_type: str, data: dict[str, Any]) -> None:
        """Send event to all subscribers. Drops dead connections."""
        if not cls._subscribers:
            return
        message = json.dumps({"type": event_type, "data": data})
        dead: list[WebSocket] = []
        for ws in list(cls._subscribers):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        async with cls._lock:
            for ws in dead:
                cls._subscribers.discard(ws)


async def emit_game_event(event_type: str, **data: Any) -> None:
    """Convenience: emit a game-related event."""
    try:
        await AdminBroker.broadcast(event_type, data)
    except Exception as e:
        logger.warning(f"WS broadcast failed: {e}")
