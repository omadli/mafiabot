"""Sandbox UserLoaderMiddleware tests.

Verifies that fake user IDs (negative range) are loaded from Redis and
NEVER trigger DB writes — the load-bearing patch for the sandbox feature.
"""

from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Chat, Update
from aiogram.types import Message as AiogramMessage
from aiogram.types import User as AiogramUser
from app.bot.middlewares.user_loader import UserLoaderMiddleware
from app.core.sandbox_ids import alloc_user_id
from app.services import transcript_store
from app.services.transcript_store import FakeUser, MemoryTranscriptBackend


@pytest.fixture(autouse=True)
def memory_backend():
    transcript_store.set_backend(MemoryTranscriptBackend())
    yield
    transcript_store.set_backend(None)


@pytest.fixture
def no_db_calls(monkeypatch):
    """Tracker that fails the test if any DB op is attempted on User/Inventory."""
    calls: list[str] = []

    async def _explode(*a, **kw):
        calls.append(f"args={a} kw={kw}")
        raise AssertionError("sandbox path must not touch DB")

    # Patch every method the real-user branch would hit.
    monkeypatch.setattr("app.bot.middlewares.user_loader.User.get_or_create", _explode)
    monkeypatch.setattr("app.bot.middlewares.user_loader.UserInventory.get_or_create", _explode)
    return calls


def _make_update_with_user(user_id: int, first_name: str = "Sandbox") -> Update:
    """Build an aiogram Update carrying a CallbackQuery from `user_id`."""
    user = AiogramUser(id=user_id, is_bot=False, first_name=first_name)
    chat = Chat(id=user_id, type="private")
    message = AiogramMessage(message_id=1, date=0, chat=chat, from_user=user, text="placeholder")
    cb = CallbackQuery(
        id="cb-1",
        from_user=user,
        chat_instance=str(user_id),
        data="noop",
        message=message,
    )
    upd = Update(update_id=1, callback_query=cb)
    # The middleware reads `.from_user` from any of `message`,
    # `callback_query`, etc. — covered by CallbackQuery being set.
    return upd


async def _passthrough(event, data):
    return data


@pytest.mark.asyncio
async def test_sandbox_user_loaded_from_redis_no_db(no_db_calls):
    sid = "sandbox-abc"
    uid = alloc_user_id(session_seq=0, player_idx=0)
    await transcript_store.set_fake_users(
        sid,
        [FakeUser(user_id=uid, first_name="Asad", username="asad_u", language_code="ru")],
    )

    middleware = UserLoaderMiddleware()
    upd = _make_update_with_user(uid)
    out: dict[str, Any] = {}
    handler: Callable[[Update, dict[str, Any]], Awaitable[Any]] = _passthrough

    await middleware(handler, upd, out)

    user = out["user"]
    assert user is not None
    assert user.id == uid
    assert user.first_name == "Asad"
    assert user.username == "asad_u"
    assert user.language_code == "ru"
    # The sandbox_id is plumbed through so downstream handlers can
    # route subsequent state ops at the right session.
    assert out["sandbox_id"] == sid
    assert no_db_calls == []  # the fixture would have raised if hit


@pytest.mark.asyncio
async def test_sandbox_user_unknown_drops_silently(no_db_calls, caplog):
    """Negative ID with no matching Redis entry must NOT fall through to
    the DB path — better to drop the update with a warning than corrupt
    `users` by attempting an insert with a negative id.
    """
    uid = alloc_user_id(session_seq=99, player_idx=0)  # nothing registered

    middleware = UserLoaderMiddleware()
    upd = _make_update_with_user(uid)
    out: dict[str, Any] = {}
    handler_was_called = {"value": False}

    async def handler(event, data):
        handler_was_called["value"] = True
        return data

    result = await middleware(handler, upd, out)
    assert result is None
    assert handler_was_called["value"] is False
    assert no_db_calls == []


@pytest.mark.asyncio
async def test_sandbox_user_not_persisted_via_save():
    """In-memory User must not attempt to INSERT itself even if some
    handler down the line calls `.save()` — `_saved_in_db=True` flips
    Tortoise into UPDATE mode (which we still avoid by sandbox guards)."""
    uid = alloc_user_id(session_seq=1, player_idx=2)
    await transcript_store.set_fake_users(
        "sid-xyz",
        [FakeUser(user_id=uid, first_name="Lola", language_code="uz")],
    )

    fake = await transcript_store.lookup_user(uid)
    user = UserLoaderMiddleware._build_sandbox_user(fake)
    assert user._saved_in_db is True  # type: ignore[attr-defined]
    # `id` survives unchanged (still negative — the CHECK constraint
    # would reject it if it ever escaped to a writer).
    assert user.id == uid


@pytest.mark.asyncio
async def test_non_sandbox_user_still_hits_db_path(monkeypatch):
    """Real positive-id users must NOT be diverted — defensive against
    the patch accidentally swallowing real traffic."""
    get_or_create_called: list[tuple] = []
    inventory_get_or_create_called: list[tuple] = []

    async def _user_goc(**kw):
        get_or_create_called.append(("user", kw))
        m = MagicMock()
        m.username = kw["defaults"]["username"]
        m.first_name = kw["defaults"]["first_name"]
        m.last_name = kw["defaults"]["last_name"]
        m.save = AsyncMock()
        return m, True

    async def _inv_goc(**kw):
        inventory_get_or_create_called.append(("inv", kw))
        return MagicMock(), True

    monkeypatch.setattr("app.bot.middlewares.user_loader.User.get_or_create", _user_goc)
    monkeypatch.setattr("app.bot.middlewares.user_loader.UserInventory.get_or_create", _inv_goc)

    middleware = UserLoaderMiddleware()
    upd = _make_update_with_user(user_id=7_300_000_000)  # real Telegram id
    out: dict[str, Any] = {}

    await middleware(_passthrough, upd, out)

    assert len(get_or_create_called) == 1
    assert len(inventory_get_or_create_called) == 1
    assert "user" in out
    assert "sandbox_id" not in out


@pytest.mark.asyncio
async def test_bot_user_is_ignored():
    middleware = UserLoaderMiddleware()
    bot_user = AiogramUser(id=999, is_bot=True, first_name="BotName")
    chat = Chat(id=-1, type="supergroup")
    message = AiogramMessage(message_id=1, date=0, chat=chat, from_user=bot_user)
    upd = Update(update_id=1, message=message)
    out: dict[str, Any] = {}

    await middleware(_passthrough, upd, out)
    assert "user" not in out
    assert "sandbox_id" not in out


@pytest.mark.asyncio
async def test_lookup_user_round_trip_in_store():
    """The reverse index used by middleware must survive a roundtrip
    through `set_fake_users`."""
    uid_a = alloc_user_id(session_seq=0, player_idx=1)
    uid_b = alloc_user_id(session_seq=0, player_idx=2)
    await transcript_store.set_fake_users(
        "sid-A",
        [
            FakeUser(user_id=uid_a, first_name="A", language_code="uz"),
            FakeUser(user_id=uid_b, first_name="B", language_code="ru"),
        ],
    )
    a = await transcript_store.lookup_user(uid_a)
    b = await transcript_store.lookup_user(uid_b)
    none = await transcript_store.lookup_user(alloc_user_id(99, 0))
    assert a["first_name"] == "A" and a["sandbox_id"] == "sid-A"
    assert b["first_name"] == "B" and b["language_code"] == "ru"
    assert none is None
