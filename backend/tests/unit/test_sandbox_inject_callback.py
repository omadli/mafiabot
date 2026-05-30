"""Tests for `sandbox_service.inject_callback`.

Verify the synthetic Update construction: a valid CallbackQuery flows
to `dp.feed_update` carrying the SandboxBot and the right user/chat
metadata. We mock the dispatcher to capture the call without booting
the bot.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.sandbox_ids import alloc_group_id, alloc_user_id
from app.services import sandbox_service, transcript_store
from app.services.recording_bot import SandboxBot, SandboxBotRegistry
from app.services.sandbox_service import SandboxError
from app.services.transcript_store import FakeUser, MemoryTranscriptBackend


@pytest.fixture(autouse=True)
def memory_backend():
    transcript_store.set_backend(MemoryTranscriptBackend())
    yield
    transcript_store.set_backend(None)
    SandboxBotRegistry.clear()


@pytest.fixture
def sandbox_setup(monkeypatch):
    """Stage a bot + a fake user + a stub SandboxSession lookup."""
    sandbox_id = uuid4()
    fake_group = alloc_group_id(0)
    fake_user = alloc_user_id(0, 0)

    bot = SandboxBot(
        sandbox_id=sandbox_id,
        fake_group_id=fake_group,
        creator_fake_user_id=fake_user,
    )
    SandboxBotRegistry.register(bot)

    # Wire the fake user into Redis (reverse-index for lookup_user).
    async def _setup():
        await transcript_store.set_fake_users(
            sandbox_id,
            [FakeUser(user_id=fake_user, first_name="Asad", language_code="ru")],
        )

    # Stub SandboxSession.get so we don't need a DB connection. `status`
    # is included so the runtime-rebuild path can classify the session
    # without touching the DB; `save` is mocked so the ERRORED-status
    # write attempt in `_ensure_runtime` doesn't try to talk to Tortoise.
    from app.db.models import SandboxStatus

    class _Stub:
        id = sandbox_id
        fake_group_id = fake_group
        status = SandboxStatus.RUNNING
        auto_play_mode = "paused"  # don't actually spawn a loop in tests

        async def save(self, **_kw):
            return None

    class _Query:
        @staticmethod
        async def get(**kw):
            assert kw["id"] == sandbox_id
            return _Stub()

    monkeypatch.setattr("app.services.sandbox_service.SandboxSession", _Query)
    return sandbox_id, fake_group, fake_user, bot, _setup


@pytest.fixture
def dispatcher_stub(monkeypatch):
    """Replace `app.main.dp` with a mock that captures feed_update calls."""
    feed_mock = AsyncMock()
    fake_dp = MagicMock()
    fake_dp.feed_update = feed_mock
    monkeypatch.setattr("app.main.dp", fake_dp, raising=False)
    return feed_mock


@pytest.mark.asyncio
async def test_inject_callback_feeds_correct_update(sandbox_setup, dispatcher_stub):
    sandbox_id, _fake_group, fake_user, bot, setup = sandbox_setup
    await setup()

    await sandbox_service.inject_callback(
        sandbox_id=sandbox_id,
        fake_user_id=fake_user,
        callback_data="night:doctor:42",
        message_id=17,
    )

    dispatcher_stub.assert_awaited_once()
    kwargs = dispatcher_stub.await_args.kwargs
    assert kwargs["bot"] is bot
    upd = kwargs["update"]
    assert upd.callback_query is not None
    cb = upd.callback_query
    assert cb.data == "night:doctor:42"
    assert cb.from_user.id == fake_user
    assert cb.from_user.first_name == "Asad"
    assert cb.from_user.language_code == "ru"
    assert cb.message.message_id == 17
    # Default chat_id == fake_user_id → DM scope.
    assert cb.message.chat.id == fake_user
    assert cb.message.chat.type == "private"


@pytest.mark.asyncio
async def test_inject_callback_group_chat_uses_supergroup_chat(sandbox_setup, dispatcher_stub):
    sandbox_id, fake_group, fake_user, _, setup = sandbox_setup
    await setup()

    await sandbox_service.inject_callback(
        sandbox_id=sandbox_id,
        fake_user_id=fake_user,
        callback_data="vote:cast:99",
        message_id=42,
        chat_id=fake_group,  # group-scope callback
    )

    cb = dispatcher_stub.await_args.kwargs["update"].callback_query
    assert cb.message.chat.id == fake_group
    assert cb.message.chat.type == "supergroup"


@pytest.mark.asyncio
async def test_inject_callback_rejects_real_user_id(sandbox_setup, dispatcher_stub):
    sandbox_id, _, _, _, _ = sandbox_setup
    with pytest.raises(SandboxError, match="not a sandbox id"):
        await sandbox_service.inject_callback(
            sandbox_id=sandbox_id,
            fake_user_id=7_300_000_000,  # real telegram-shaped id
            callback_data="vote:cast:1",
            message_id=1,
        )
    dispatcher_stub.assert_not_awaited()


@pytest.mark.asyncio
async def test_inject_callback_rebuilds_runtime_when_bot_missing(sandbox_setup, dispatcher_stub):
    """After a backend restart the SandboxBotRegistry is empty even though
    the session is still RUNNING. `inject_callback` should rebuild the
    runtime so the operator can keep driving the existing sandbox without
    losing its transcript.

    Here we exercise the failure-to-rebuild case: the Redis GameState was
    also lost (TTL or eviction), so the rebuild can't proceed — we
    expect a clear "destroy + recreate" error rather than the cryptic
    "no live bot" surface the old code produced.
    """
    sandbox_id, fake_group, fake_user, _, setup = sandbox_setup
    await setup()
    SandboxBotRegistry.unregister(fake_group)

    with pytest.raises(SandboxError, match="lost its Redis state"):
        await sandbox_service.inject_callback(
            sandbox_id=sandbox_id,
            fake_user_id=fake_user,
            callback_data="x",
            message_id=1,
        )
    dispatcher_stub.assert_not_awaited()


@pytest.mark.asyncio
async def test_inject_callback_rejects_when_fake_user_unknown(sandbox_setup, dispatcher_stub):
    sandbox_id, _, _, _, _ = sandbox_setup
    # Skip await setup() so the reverse index is empty.
    rogue_uid = alloc_user_id(0, 5)
    with pytest.raises(SandboxError, match="missing from sandbox"):
        await sandbox_service.inject_callback(
            sandbox_id=sandbox_id,
            fake_user_id=rogue_uid,
            callback_data="x",
            message_id=1,
        )
    dispatcher_stub.assert_not_awaited()


@pytest.mark.asyncio
async def test_inject_callback_rejects_when_dispatcher_missing(sandbox_setup, monkeypatch):
    sandbox_id, _, fake_user, _, setup = sandbox_setup
    await setup()
    monkeypatch.setattr("app.main.dp", None, raising=False)
    with pytest.raises(SandboxError, match="dispatcher not initialized"):
        await sandbox_service.inject_callback(
            sandbox_id=sandbox_id,
            fake_user_id=fake_user,
            callback_data="x",
            message_id=1,
        )


@pytest.mark.asyncio
async def test_inject_callback_update_id_is_unique(sandbox_setup, dispatcher_stub):
    sandbox_id, _, fake_user, _, setup = sandbox_setup
    await setup()

    await sandbox_service.inject_callback(sandbox_id, fake_user, "x", 1)
    await sandbox_service.inject_callback(sandbox_id, fake_user, "y", 2)
    await sandbox_service.inject_callback(sandbox_id, fake_user, "z", 3)

    update_ids = [call.kwargs["update"].update_id for call in dispatcher_stub.await_args_list]
    assert len(set(update_ids)) == 3  # all unique
