# ruff: noqa: UP047
#
# The three fan-out helpers below (`safe_send`, `paced_each`,
# `paced_gather`) are generic over T. Ruff's UP047 wants the PEP 695
# `async def fn[T](...)` form, but mypy 1.x doesn't support PEP 695
# generics outside its experimental flag (see CI logs). Until mypy
# catches up, keep the legacy `TypeVar` shape and silence the rule
# at the file level.

"""Telegram-friendly wrappers around the bot's send methods.

Why this file exists
====================

Every place we DM more than a handful of users at once — role reveals
at game start, voting prompts to 30 alive players, mafia-chat fan-out
— used to be `await asyncio.gather(*coros)`. That bursts the entire
batch at once and trips Telegram's 30 msg/s bot-wide limit the moment
two games start in the same second. The first time we noticed was
when the broadcast feature shipped: a 10 000-user push at full throttle
crashed with cascading `TelegramRetryAfter`.

This module centralises three concerns so the call sites stay simple:

1. **Pacing.** `paced_gather(coros, delay)` runs the awaitables one
   at a time with a sleep between them. 0.1 s = 10 msg/s, well under
   the 30 msg/s bot-wide cap with comfortable headroom for the engine's
   other traffic.

2. **Retry on 429.** `safe_send(coro_factory)` catches
   `TelegramRetryAfter`, sleeps the server-supplied `retry_after`
   (plus a fudge second), and retries once. Two retries would be
   nice-to-have, but a single retry already absorbs the common case
   without compounding back-pressure.

3. **Mark unreachable users.** `TelegramForbiddenError` and
   `user is deactivated` mean the recipient can't be reached by any
   future bot call. We flip `User.is_active=False` so the broadcast
   queue, the role-DM dispatcher, and anything else that fans out
   stops wasting request slots.

Importantly, `safe_send` accepts a `coro_factory` (a zero-arg callable
returning a fresh coroutine) rather than an already-awaited coroutine.
Awaiting twice is a runtime error; retries need a fresh coroutine
each time.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from loguru import logger

from app.db.models import User

# Generic type parameter used by the three fan-out helpers below. Kept
# as `TypeVar` rather than the PEP 695 `[T]` syntax because mypy 1.x
# doesn't support the new syntax outside its experimental flag; ruff's
# UP047 hint is silenced per-function with `noqa`.
T = TypeVar("T")

# Default pacing between sends in a fan-out batch. Picked so a single
# game's 30-player role-DM batch finishes in ~3 s (acceptable for the
# operator), well below the 30 msg/s bot-wide limit even when two games
# overlap, and slow enough that the broadcast worker leaves headroom
# for in-flight game traffic.
DEFAULT_DELAY_SECONDS = 0.1

# Cap on retry_after we'll honour. Telegram occasionally returns
# multi-minute backoffs during outages; if we hit one, fail fast rather
# than block the whole batch on a single stuck recipient.
MAX_RETRY_AFTER_SECONDS = 30.0


class SendResult:
    """Outcome of a single safe-send.

    Used by the broadcast worker to classify failures and by
    `paced_gather` to surface per-recipient results without raising.
    Lightweight tuple-like helper — defining a class so the call sites
    can match `result.ok` instead of magic strings.
    """

    __slots__ = ("exc", "ok", "reason", "value")

    def __init__(
        self,
        ok: bool,
        reason: str | None = None,
        exc: Exception | None = None,
        value: object | None = None,
    ) -> None:
        self.ok = ok
        self.reason = (
            reason  # 'forbidden' | 'deactivated' | 'bad_request' | 'retry_after' | 'other'
        )
        self.exc = exc
        self.value = value  # the return value of the underlying call when ok

    def __repr__(self) -> str:
        return f"SendResult(ok={self.ok}, reason={self.reason!r})"


def _classify_bad_request(exc: TelegramBadRequest) -> str:
    """Map BadRequest message text → a coarse reason bucket.

    Telegram doesn't expose a structured error code; we sniff the
    description for the few cases the broadcaster needs to act on
    differently (deactivated accounts should still flip `is_active`,
    other bad-requests shouldn't).
    """
    msg = str(exc).lower()
    if "user is deactivated" in msg or "chat not found" in msg:
        return "deactivated"
    return "bad_request"


async def _mark_inactive(user_id: int, reason: str) -> None:
    """Flip `users.is_active = False` for a user the bot can't reach."""
    try:
        await User.filter(id=user_id).update(
            is_active=False,
            inactive_reason=reason,
            inactive_at=datetime.now(UTC),
        )
    except Exception as e:
        logger.debug(f"safe_messaging: failed to mark user {user_id} inactive: {e}")


async def safe_send(
    coro_factory: Callable[[], Awaitable[T]],
    *,
    target_user_id: int | None = None,
    retry_429: bool = True,
) -> SendResult:
    """Invoke a single bot send call with 429-retry + inactive-marking.

    Args:
        coro_factory: zero-arg callable returning a fresh coroutine.
            Required (not an awaitable) so we can rebuild on retry.
        target_user_id: when set, a TelegramForbidden / deactivated
            error flips `users.is_active = False` for this user.
            Pass `None` for sends to groups or other non-user chats.
        retry_429: if True, transparently retries once on
            `TelegramRetryAfter` after sleeping the server-supplied
            retry-after window. Defaults to True; callers in tight
            loops where they manage their own backoff can disable it.

    Returns:
        `SendResult.ok=True` with `value=<return of the send>` on
        success; otherwise `ok=False` with a `reason` bucket and the
        underlying exception. Never raises — fan-out callers can
        aggregate results without try/except per recipient.
    """
    try:
        value = await coro_factory()
        return SendResult(ok=True, value=value)
    except TelegramRetryAfter as e:
        wait = min(float(e.retry_after) + 1.0, MAX_RETRY_AFTER_SECONDS)
        logger.warning(
            f"safe_send: 429 from Telegram, sleeping {wait:.1f}s (user={target_user_id})"
        )
        if not retry_429:
            return SendResult(ok=False, reason="retry_after", exc=e)
        await asyncio.sleep(wait)
        try:
            value = await coro_factory()
            return SendResult(ok=True, value=value)
        except Exception as inner:
            return SendResult(ok=False, reason="other", exc=inner)
    except TelegramForbiddenError as e:
        if target_user_id is not None:
            await _mark_inactive(target_user_id, "forbidden")
        return SendResult(ok=False, reason="forbidden", exc=e)
    except TelegramBadRequest as e:
        reason = _classify_bad_request(e)
        if reason == "deactivated" and target_user_id is not None:
            await _mark_inactive(target_user_id, "deactivated")
        return SendResult(ok=False, reason=reason, exc=e)
    except Exception as e:
        logger.debug(f"safe_send: unexpected error (user={target_user_id}): {e}")
        return SendResult(ok=False, reason="other", exc=e)


async def paced_each(
    items: list[T],
    send: Callable[[T], Awaitable[Any]],
    *,
    delay: float = DEFAULT_DELAY_SECONDS,
    user_id_of: Callable[[T], int | None] | None = None,
) -> list[SendResult]:
    """Looser-typed convenience wrapper for the common DM fan-out shape.

    Where `paced_gather` requires the caller to pre-build a list of
    `(coro_factory, user_id)` tuples, `paced_each` accepts the
    recipient list directly + a `send(item)` async callable. We
    re-invoke the callable each time so a retry inside `safe_send`
    starts from a fresh coroutine.

    `user_id_of` lets us flip `User.is_active=False` when the
    recipient is a user (vs. a group/chat). For PlayerState lists
    pass `lambda p: p.user_id`; for raw int IDs pass `lambda x: x`;
    omit it for non-user targets.
    """
    out: list[SendResult] = []
    for idx, item in enumerate(items):
        target = user_id_of(item) if user_id_of else None

        def _make(_it: T = item) -> Callable[[], Awaitable[Any]]:
            return lambda: send(_it)

        result = await safe_send(_make(), target_user_id=target)
        out.append(result)
        if idx + 1 < len(items):
            await asyncio.sleep(delay)
    return out


async def paced_gather(
    coro_factories: list[tuple[Callable[[], Awaitable[T]], int | None]],
    *,
    delay: float = DEFAULT_DELAY_SECONDS,
    retry_429: bool = True,
) -> list[SendResult]:
    """Sequential equivalent of `asyncio.gather` with a fixed delay.

    Each entry is `(coro_factory, target_user_id)`. Sends run one at
    a time with `delay` seconds between them. Per-send 429 retries
    still apply via `safe_send`. Returns the list of `SendResult`s
    in the same order the factories were given.

    Use over `asyncio.gather` whenever the batch size can exceed the
    bot's 30-msg/s budget — role-DM dispatch at game start, per-player
    voting prompts, broadcast worker, etc. For batches of 2-3 sends
    `asyncio.gather` is still fine; pacing is not free.
    """
    out: list[SendResult] = []
    for idx, (factory, target_user_id) in enumerate(coro_factories):
        result = await safe_send(factory, target_user_id=target_user_id, retry_429=retry_429)
        out.append(result)
        # Skip the trailing sleep after the last send.
        if idx + 1 < len(coro_factories):
            await asyncio.sleep(delay)
    return out
