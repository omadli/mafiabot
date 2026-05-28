"""Tests for the sandbox transcript store (Redis layer only).

DB dump path is exercised in the integration tests where a real
Tortoise connection is available; here we focus on the in-memory
backend semantics so the tests are hermetic and fast.
"""

from uuid import uuid4

import pytest
from app.services import transcript_store as ts
from app.services.transcript_store import (
    SESSION_TTL_SECONDS,
    TRANSCRIPT_HARD_CAP,
    FakeUser,
    MemoryTranscriptBackend,
    TranscriptEntry,
)


@pytest.fixture(autouse=True)
def memory_backend():
    backend = MemoryTranscriptBackend()
    ts.set_backend(backend)
    yield backend
    ts.set_backend(None)


@pytest.fixture
def sid():
    return uuid4()


@pytest.mark.asyncio
async def test_next_message_id_is_monotonic(sid):
    a = await ts.next_message_id(sid)
    b = await ts.next_message_id(sid)
    c = await ts.next_message_id(sid)
    assert (a, b, c) == (1, 2, 3)


@pytest.mark.asyncio
async def test_next_message_id_is_per_session(sid):
    other = uuid4()
    a = await ts.next_message_id(sid)
    b = await ts.next_message_id(other)
    assert a == 1 and b == 1  # independent counters


@pytest.mark.asyncio
async def test_append_assigns_seq_and_ts(sid):
    e = TranscriptEntry(type="send", chat_id=-1, message_id=1, text="hi")
    out = await ts.append(sid, e)
    assert out.seq == 1
    assert out.ts > 0


@pytest.mark.asyncio
async def test_append_preserves_explicit_seq(sid):
    e = TranscriptEntry(seq=42, type="send", chat_id=-1, message_id=1)
    out = await ts.append(sid, e)
    assert out.seq == 42  # caller-supplied seq honoured


@pytest.mark.asyncio
async def test_append_then_range_round_trip(sid):
    for i in range(5):
        await ts.append(sid, TranscriptEntry(type="send", chat_id=-1, message_id=i, text=f"msg{i}"))
    entries = await ts.range_(sid)
    assert [e.text for e in entries] == ["msg0", "msg1", "msg2", "msg3", "msg4"]
    assert [e.seq for e in entries] == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_range_since_seq_skips_older(sid):
    for i in range(5):
        await ts.append(sid, TranscriptEntry(type="send", chat_id=-1, message_id=i))
    entries = await ts.range_(sid, since_seq=2)
    # Only entries with seq > 2 → seqs 3, 4, 5.
    assert [e.seq for e in entries] == [3, 4, 5]


@pytest.mark.asyncio
async def test_range_limit_is_respected(sid):
    for i in range(10):
        await ts.append(sid, TranscriptEntry(type="send", chat_id=-1, message_id=i))
    entries = await ts.range_(sid, since_seq=0, limit=3)
    assert len(entries) == 3
    assert [e.seq for e in entries] == [1, 2, 3]


@pytest.mark.asyncio
async def test_hard_cap_trims_oldest(sid, memory_backend):
    # Push more than the cap; oldest should be discarded.
    overflow = 5
    for i in range(TRANSCRIPT_HARD_CAP + overflow):
        await ts.append(sid, TranscriptEntry(type="send", chat_id=-1, message_id=i))
    assert await ts.llen(sid) == TRANSCRIPT_HARD_CAP
    # Earliest surviving entry has seq == overflow + 1 (1-indexed).
    entries = await ts.range_(sid, since_seq=0, limit=1)
    assert entries[0].seq == overflow + 1


@pytest.mark.asyncio
async def test_set_and_get_meta(sid):
    meta = {"sandbox_id": str(sid), "n_players": 8, "auto_play_mode": "paused"}
    await ts.set_meta(sid, meta)
    got = await ts.get_meta(sid)
    assert got == meta


@pytest.mark.asyncio
async def test_get_meta_missing_returns_none(sid):
    assert await ts.get_meta(sid) is None


@pytest.mark.asyncio
async def test_fake_user_round_trip(sid):
    users = [
        FakeUser(user_id=-1, first_name="Asad", language_code="uz"),
        FakeUser(user_id=-2, first_name="Lola", username="lolka", language_code="ru"),
    ]
    await ts.set_fake_users(sid, users)
    listed = await ts.list_fake_users(sid)
    assert {u.user_id for u in listed} == {-1, -2}
    one = await ts.get_fake_user(sid, -2)
    assert one is not None and one.first_name == "Lola" and one.language_code == "ru"


@pytest.mark.asyncio
async def test_get_fake_user_missing(sid):
    await ts.set_fake_users(sid, [FakeUser(user_id=-1, first_name="A")])
    assert await ts.get_fake_user(sid, -999) is None


@pytest.mark.asyncio
async def test_clear_removes_every_key(sid, memory_backend):
    await ts.append(sid, TranscriptEntry(type="send", chat_id=-1, message_id=1))
    await ts.next_message_id(sid)
    await ts.set_meta(sid, {"x": 1})
    await ts.set_fake_users(sid, [FakeUser(user_id=-1, first_name="A")])

    await ts.clear(sid)

    assert await ts.llen(sid) == 0
    assert await ts.get_meta(sid) is None
    assert await ts.list_fake_users(sid) == []
    # Counter is also gone — next call starts at 1 again.
    assert await ts.next_message_id(sid) == 1


@pytest.mark.asyncio
async def test_ttls_refreshed_on_writes(sid, memory_backend):
    """TTL refresh is best-effort but must be applied at least once."""
    await ts.append(sid, TranscriptEntry(type="send", chat_id=-1, message_id=1))
    await ts.next_message_id(sid)
    await ts.set_meta(sid, {})
    await ts.set_fake_users(sid, [FakeUser(user_id=-1, first_name="A")])

    ttls = memory_backend._ttls
    # Every persisted key should have a TTL ≈ 24 h.
    for key, ttl in ttls.items():
        assert ttl == SESSION_TTL_SECONDS, f"TTL mismatch for {key}: {ttl}"
    # And every key we wrote is tracked.
    expected_keys = {
        f"mafia:sandbox:{sid}:transcript",
        f"mafia:sandbox:{sid}:next_msg_id",
        f"mafia:sandbox:{sid}:next_seq",
        f"mafia:sandbox:{sid}:meta",
        f"mafia:sandbox:{sid}:fake_users",
    }
    assert expected_keys.issubset(set(ttls.keys()))


@pytest.mark.asyncio
async def test_transcript_entry_json_round_trip():
    e = TranscriptEntry(
        seq=7,
        ts=1234567890.5,
        type="send",
        scope="dm",
        chat_id=-42,
        target_user_id=-42,
        message_id=3,
        text="hello",
        parse_mode="HTML",
        reply_markup={"inline_keyboard": [[{"text": "ok", "callback_data": "ok"}]]},
    )
    restored = TranscriptEntry.from_json(e.to_json())
    assert restored == e
