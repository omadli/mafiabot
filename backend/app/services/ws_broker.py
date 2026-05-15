"""WebSocket broker — broadcast game events to admin / SA subscribers.

Two flavours of subscription:
- Global: all events flow here (used by the admin dashboard activity feed).
- Per-group: only events tagged with `group_id` flow here. Used by the
  live-game spectator page so we don't flood a viewer's socket with
  unrelated games.

emit_game_event(event_type, group_id=..., **data) routes to:
  - global subscribers always
  - per-group subscribers IFF group_id is non-None and matches
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, ClassVar

from fastapi import WebSocket
from loguru import logger


class AdminBroker:
    """In-memory pub/sub for admin WS subscribers."""

    _global: ClassVar[set[WebSocket]] = set()
    _by_group: ClassVar[dict[int, set[WebSocket]]] = {}
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    @classmethod
    async def subscribe(cls, ws: WebSocket, group_id: int | None = None) -> None:
        async with cls._lock:
            if group_id is None:
                cls._global.add(ws)
            else:
                cls._by_group.setdefault(group_id, set()).add(ws)
        scope = "global" if group_id is None else f"group:{group_id}"
        logger.debug(f"WS subscribed to {scope}")

    @classmethod
    async def unsubscribe(cls, ws: WebSocket, group_id: int | None = None) -> None:
        async with cls._lock:
            if group_id is None:
                cls._global.discard(ws)
            else:
                bucket = cls._by_group.get(group_id)
                if bucket is not None:
                    bucket.discard(ws)
                    if not bucket:
                        cls._by_group.pop(group_id, None)

    @classmethod
    async def broadcast(
        cls,
        event_type: str,
        data: dict[str, Any],
        group_id: int | None = None,
    ) -> None:
        """Send event to global + (optionally) per-group subscribers."""
        message = json.dumps({"type": event_type, "data": data})
        targets: list[WebSocket] = list(cls._global)
        if group_id is not None:
            targets.extend(cls._by_group.get(group_id, set()))
        if not targets:
            return
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with cls._lock:
                for ws in dead:
                    cls._global.discard(ws)
                    for bucket in cls._by_group.values():
                        bucket.discard(ws)


async def emit_game_event(event_type: str, group_id: int | None = None, **data: Any) -> None:
    """Convenience wrapper for game-state event emission.

    Always includes group_id in payload (when supplied) so global-channel
    subscribers can route client-side too.
    """
    if group_id is not None:
        data.setdefault("group_id", group_id)
    try:
        await AdminBroker.broadcast(event_type, data, group_id=group_id)
    except Exception as e:
        logger.warning(f"WS broadcast failed: {e}")
