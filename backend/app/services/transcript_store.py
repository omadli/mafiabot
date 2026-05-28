"""Redis-resident sandbox transcript store.

Holds the live stream of bot sends/edits/deletes captured by
`SandboxBot`. Persists to Postgres only on session finish — the live
panel reads from Redis for low-latency streaming.

Key layout (per sandbox session, keyed by UUID `sid`):

    mafia:sandbox:{sid}:transcript    — Redis LIST (RPUSH entries, JSON)
    mafia:sandbox:{sid}:next_msg_id   — INCR counter (synthetic message_id)
    mafia:sandbox:{sid}:next_seq      — INCR counter (monotonic transcript seq)
    mafia:sandbox:{sid}:meta          — JSON (sandbox metadata)
    mafia:sandbox:{sid}:fake_users    — HASH (user_id_str → JSON user dict)
    mafia:sandbox:user:{uid}          — JSON {sandbox_id, first_name, ...}
                                        (reverse index for middleware lookups)

All keys carry a 24 h TTL refreshed on every write — a sandbox that's
idle for a day is reaped automatically; the DB row in
`sandbox_sessions` keeps the post-mortem snapshot for history.

Backend abstraction mirrors `app.core.redis_state.StateBackend` so
tests can swap in an in-memory implementation without touching Redis.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol
from uuid import UUID

from loguru import logger

# 24 h TTL, refreshed on every write.
SESSION_TTL_SECONDS = 24 * 3600
# Hard cap on transcript entries kept in Redis per session.
# Older entries are trimmed; they survive in the DB once session finishes.
TRANSCRIPT_HARD_CAP = 5000


@dataclass
class TranscriptEntry:
    """In-memory shape of a single transcript row.

    Mirrors `SandboxTranscriptEntry` DB model columns plus a `seq` that
    the store assigns on append. Pure dataclass (not Pydantic) for speed
    and trivial JSON round-tripping.
    """

    seq: int = 0  # assigned by `append` if 0
    ts: float = 0.0  # unix timestamp; set by `append` if 0
    type: str = "send"
    scope: str = "group"
    chat_id: int = 0
    target_user_id: int | None = None
    message_id: int = 0
    ref_message_id: int | None = None
    text: str | None = None
    parse_mode: str | None = None
    reply_markup: dict[str, Any] | None = None
    media: dict[str, Any] | None = None
    # Sandbox-only enrichment for the dashboard; not persisted as columns.
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> TranscriptEntry:
        return cls(**json.loads(raw))


@dataclass
class FakeUser:
    """In-memory representation of a sandbox fake player."""

    user_id: int
    first_name: str
    username: str | None = None
    language_code: str = "uz"

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> FakeUser:
        return cls(**json.loads(raw))


# Redis key helpers — single source of truth so backends and tests agree.
def _k_transcript(sid: UUID | str) -> str:
    return f"mafia:sandbox:{sid}:transcript"


def _k_next_msg_id(sid: UUID | str) -> str:
    return f"mafia:sandbox:{sid}:next_msg_id"


def _k_next_seq(sid: UUID | str) -> str:
    return f"mafia:sandbox:{sid}:next_seq"


def _k_meta(sid: UUID | str) -> str:
    return f"mafia:sandbox:{sid}:meta"


def _k_fake_users(sid: UUID | str) -> str:
    return f"mafia:sandbox:{sid}:fake_users"


def _k_user_reverse(uid: int) -> str:
    """Reverse-index key: fake user_id → which sandbox they belong to."""
    return f"mafia:sandbox:user:{uid}"


def all_keys_for(sid: UUID | str, user_ids: list[int] | None = None) -> list[str]:
    """Every Redis key owned by this sandbox session (used by `clear`).

    Pass `user_ids` to also include the reverse-index entries for those
    fake users — otherwise the reverse index is left dangling. Callers
    that don't track the user list should fall back to `clear_with_users`.
    """
    keys = [
        _k_transcript(sid),
        _k_next_msg_id(sid),
        _k_next_seq(sid),
        _k_meta(sid),
        _k_fake_users(sid),
    ]
    if user_ids:
        keys.extend(_k_user_reverse(uid) for uid in user_ids)
    return keys


class TranscriptBackend(Protocol):
    """Minimal subset of redis.asyncio operations the store needs."""

    async def rpush(self, key: str, *values: str) -> int: ...
    async def lrange(self, key: str, start: int, end: int) -> list[str]: ...
    async def ltrim(self, key: str, start: int, end: int) -> None: ...
    async def llen(self, key: str) -> int: ...
    async def incr(self, key: str) -> int: ...
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> None: ...
    async def delete(self, *keys: str) -> int: ...
    async def hset(self, key: str, field: str, value: str) -> int: ...
    async def hget(self, key: str, field: str) -> str | None: ...
    async def hgetall(self, key: str) -> dict[str, str]: ...
    async def expire(self, key: str, ttl: int) -> None: ...


class MemoryTranscriptBackend:
    """In-memory backend for tests — no real Redis needed."""

    def __init__(self) -> None:
        self._lists: dict[str, list[str]] = {}
        self._kv: dict[str, str] = {}
        self._hashes: dict[str, dict[str, str]] = {}
        self._counters: dict[str, int] = {}
        self._ttls: dict[str, int] = {}  # for assertions; not enforced

    async def rpush(self, key: str, *values: str) -> int:
        lst = self._lists.setdefault(key, [])
        lst.extend(values)
        return len(lst)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        lst = self._lists.get(key, [])
        # Redis LRANGE is inclusive on both ends; -1 means "last".
        if end == -1:
            return lst[start:]
        return lst[start : end + 1]

    async def ltrim(self, key: str, start: int, end: int) -> None:
        lst = self._lists.get(key)
        if lst is None:
            return
        if end == -1:
            self._lists[key] = lst[start:]
        else:
            self._lists[key] = lst[start : end + 1]

    async def llen(self, key: str) -> int:
        return len(self._lists.get(key, []))

    async def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    async def get(self, key: str) -> str | None:
        return self._kv.get(key)

    async def set(self, key: str, value: str) -> None:
        self._kv[key] = value

    async def delete(self, *keys: str) -> int:
        n = 0
        for k in keys:
            if k in self._kv:
                del self._kv[k]
                n += 1
            if k in self._lists:
                del self._lists[k]
                n += 1
            if k in self._hashes:
                del self._hashes[k]
                n += 1
            if k in self._counters:
                del self._counters[k]
                n += 1
            if k in self._ttls:
                del self._ttls[k]
        return n

    async def hset(self, key: str, field: str, value: str) -> int:
        h = self._hashes.setdefault(key, {})
        new = field not in h
        h[field] = value
        return 1 if new else 0

    async def hget(self, key: str, field: str) -> str | None:
        return self._hashes.get(key, {}).get(field)

    async def hgetall(self, key: str) -> dict[str, str]:
        return dict(self._hashes.get(key, {}))

    async def expire(self, key: str, ttl: int) -> None:
        self._ttls[key] = ttl


class RedisTranscriptBackend:
    """Production backend — wraps `redis.asyncio` client."""

    def __init__(self, url: str) -> None:
        from redis.asyncio import from_url

        self._c = from_url(url, decode_responses=True)

    async def rpush(self, key: str, *values: str) -> int:
        return await self._c.rpush(key, *values)  # type: ignore[misc]

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        return await self._c.lrange(key, start, end)  # type: ignore[misc]

    async def ltrim(self, key: str, start: int, end: int) -> None:
        await self._c.ltrim(key, start, end)  # type: ignore[misc]

    async def llen(self, key: str) -> int:
        return await self._c.llen(key)  # type: ignore[misc]

    async def incr(self, key: str) -> int:
        return await self._c.incr(key)  # type: ignore[misc]

    async def get(self, key: str) -> str | None:
        return await self._c.get(key)  # type: ignore[misc]

    async def set(self, key: str, value: str) -> None:
        await self._c.set(key, value)  # type: ignore[misc]

    async def delete(self, *keys: str) -> int:
        return await self._c.delete(*keys)  # type: ignore[misc]

    async def hset(self, key: str, field: str, value: str) -> int:
        return await self._c.hset(key, field, value)  # type: ignore[misc]

    async def hget(self, key: str, field: str) -> str | None:
        return await self._c.hget(key, field)  # type: ignore[misc]

    async def hgetall(self, key: str) -> dict[str, str]:
        return await self._c.hgetall(key)  # type: ignore[misc]

    async def expire(self, key: str, ttl: int) -> None:
        await self._c.expire(key, ttl)


_backend: TranscriptBackend | None = None


def get_backend() -> TranscriptBackend:
    """Lazy backend singleton — mirrors `redis_state.get_state_backend`."""
    global _backend
    if _backend is not None:
        return _backend
    from app.config import settings

    if settings.fsm_storage == "memory":
        _backend = MemoryTranscriptBackend()
    else:
        _backend = RedisTranscriptBackend(settings.redis_url)
    return _backend


def set_backend(backend: TranscriptBackend | None) -> None:
    """Override the backend (for tests). Pass `None` to reset to lazy default."""
    global _backend
    _backend = backend


# === High-level API ============================================================


async def next_message_id(sid: UUID | str) -> int:
    """Allocate the next synthetic `Message.message_id` for this session."""
    b = get_backend()
    msg_id = await b.incr(_k_next_msg_id(sid))
    await b.expire(_k_next_msg_id(sid), SESSION_TTL_SECONDS)
    return msg_id


async def append(sid: UUID | str, entry: TranscriptEntry) -> TranscriptEntry:
    """Append an entry to the live transcript.

    Assigns `seq` and `ts` if unset, RPUSHes, refreshes TTL, and trims
    to `TRANSCRIPT_HARD_CAP` so a runaway sandbox can't blow up Redis.
    Returns the entry with `seq`/`ts` populated so callers can emit WS
    events without a re-read.
    """
    b = get_backend()
    if entry.seq == 0:
        entry.seq = await b.incr(_k_next_seq(sid))
        await b.expire(_k_next_seq(sid), SESSION_TTL_SECONDS)
    if entry.ts == 0:
        entry.ts = time.time()
    key = _k_transcript(sid)
    n = await b.rpush(key, entry.to_json())
    await b.expire(key, SESSION_TTL_SECONDS)
    if n > TRANSCRIPT_HARD_CAP:
        # Drop the oldest overflow — DB snapshot on finish preserves history.
        await b.ltrim(key, -TRANSCRIPT_HARD_CAP, -1)
    return entry


async def range_(sid: UUID | str, since_seq: int = 0, limit: int = 200) -> list[TranscriptEntry]:
    """Fetch a window of entries with `seq > since_seq`, oldest first.

    `since_seq=0` returns from the beginning. Caller paginates by
    passing the last returned `seq` as the next `since_seq`.
    """
    b = get_backend()
    raw = await b.lrange(_k_transcript(sid), 0, -1)
    out: list[TranscriptEntry] = []
    for s in raw:
        e = TranscriptEntry.from_json(s)
        if e.seq > since_seq:
            out.append(e)
            if len(out) >= limit:
                break
    return out


async def llen(sid: UUID | str) -> int:
    return await get_backend().llen(_k_transcript(sid))


async def set_meta(sid: UUID | str, meta: dict[str, Any]) -> None:
    b = get_backend()
    await b.set(_k_meta(sid), json.dumps(meta, separators=(",", ":"), ensure_ascii=False))
    await b.expire(_k_meta(sid), SESSION_TTL_SECONDS)


async def get_meta(sid: UUID | str) -> dict[str, Any] | None:
    raw = await get_backend().get(_k_meta(sid))
    if raw is None:
        return None
    return json.loads(raw)


async def set_fake_users(sid: UUID | str, users: list[FakeUser]) -> None:
    """Replace the per-session fake-user table + write the reverse index.

    The reverse index lets the UserLoader middleware go directly from
    fake user_id → sandbox_id without scanning every session — critical
    because middleware fires on every Telegram update.
    """
    b = get_backend()
    key = _k_fake_users(sid)
    # No HMSET in the protocol surface; serial HSETs are fine for ≤30 users.
    for u in users:
        await b.hset(key, str(u.user_id), u.to_json())
        # Reverse index: a JSON blob that bundles the sandbox_id with the
        # user metadata so the middleware needs exactly one Redis call.
        reverse = {
            "sandbox_id": str(sid),
            "user_id": u.user_id,
            "first_name": u.first_name,
            "username": u.username,
            "language_code": u.language_code,
        }
        await b.set(
            _k_user_reverse(u.user_id),
            json.dumps(reverse, separators=(",", ":"), ensure_ascii=False),
        )
        await b.expire(_k_user_reverse(u.user_id), SESSION_TTL_SECONDS)
    await b.expire(key, SESSION_TTL_SECONDS)


async def get_fake_user(sid: UUID | str, user_id: int) -> FakeUser | None:
    raw = await get_backend().hget(_k_fake_users(sid), str(user_id))
    if raw is None:
        return None
    return FakeUser.from_json(raw)


async def list_fake_users(sid: UUID | str) -> list[FakeUser]:
    raw = await get_backend().hgetall(_k_fake_users(sid))
    return [FakeUser.from_json(v) for v in raw.values()]


async def lookup_user(user_id: int) -> dict[str, Any] | None:
    """Reverse-lookup a fake user by user_id alone.

    Returns the dict written by `set_fake_users` (with `sandbox_id`,
    `first_name`, `username`, `language_code`) or None if the ID isn't
    registered in any active sandbox. Used by the user-loader middleware
    on every Telegram update — must be a single Redis round-trip.
    """
    raw = await get_backend().get(_k_user_reverse(user_id))
    if raw is None:
        return None
    return json.loads(raw)


async def clear(sid: UUID | str, user_ids: list[int] | None = None) -> None:
    """Drop every Redis key belonging to this session.

    Pass `user_ids` to also clear the reverse-index entries (otherwise
    they survive TTL but are no longer reachable from the session).
    Called on stop/destroy after `dump_to_db` has snapshotted to Postgres.
    """
    await get_backend().delete(*all_keys_for(sid, user_ids=user_ids))


async def dump_to_db(sid: UUID | str, session_id: UUID) -> dict[str, int]:
    """Persist the entire Redis transcript to `sandbox_transcript_entries`.

    Returns a summary dict ready to drop into `SandboxSession.transcript_summary`:
        {n_entries, group_msg_count, dm_msg_count, mafia_chat_count, dead_chat_count}

    Uses Tortoise `bulk_create` for a single round-trip. Idempotent
    against an empty transcript (returns zeros).
    """
    from datetime import UTC, datetime

    from app.db.models import SandboxTranscriptEntry, TranscriptEntryType, TranscriptScope

    b = get_backend()
    raw = await b.lrange(_k_transcript(sid), 0, -1)
    if not raw:
        return {
            "n_entries": 0,
            "group_msg_count": 0,
            "dm_msg_count": 0,
            "mafia_chat_count": 0,
            "dead_chat_count": 0,
        }

    rows: list[SandboxTranscriptEntry] = []
    summary = {
        "n_entries": 0,
        "group_msg_count": 0,
        "dm_msg_count": 0,
        "mafia_chat_count": 0,
        "dead_chat_count": 0,
    }
    for s in raw:
        e = TranscriptEntry.from_json(s)
        rows.append(
            SandboxTranscriptEntry(
                session_id=session_id,
                seq=e.seq,
                ts=datetime.fromtimestamp(e.ts, tz=UTC),
                type=TranscriptEntryType(e.type),
                scope=TranscriptScope(e.scope),
                chat_id=e.chat_id,
                target_user_id=e.target_user_id,
                message_id=e.message_id,
                ref_message_id=e.ref_message_id,
                text=e.text,
                parse_mode=e.parse_mode,
                reply_markup=e.reply_markup,
                media=e.media,
            )
        )
        summary["n_entries"] += 1
        if e.scope == "group":
            summary["group_msg_count"] += 1
        elif e.scope == "dm":
            summary["dm_msg_count"] += 1
        elif e.scope == "mafia_chat":
            summary["mafia_chat_count"] += 1
        elif e.scope == "dead_chat":
            summary["dead_chat_count"] += 1

    try:
        await SandboxTranscriptEntry.bulk_create(rows, batch_size=500)
    except Exception:
        logger.exception(f"transcript dump_to_db failed for session={session_id}")
        raise
    return summary
