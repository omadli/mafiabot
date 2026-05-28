"""Tests for SandboxBot — duck-typed Telegram Bot for sandbox sessions."""

from uuid import uuid4

import pytest
from app.core.sandbox_ids import alloc_group_id, alloc_user_id
from app.services import transcript_store as ts
from app.services.recording_bot import (
    SandboxBot,
    SandboxBotRegistry,
    _scope_for,
    _serialize_keyboard,
)
from app.services.transcript_store import MemoryTranscriptBackend


@pytest.fixture(autouse=True)
def memory_backend():
    backend = MemoryTranscriptBackend()
    ts.set_backend(backend)
    yield backend
    ts.set_backend(None)
    SandboxBotRegistry.clear()


@pytest.fixture
def sandbox():
    sid = uuid4()
    fake_group = alloc_group_id(session_seq=0)
    creator = alloc_user_id(session_seq=0, player_idx=0)
    return sid, fake_group, creator


@pytest.fixture
def bot(sandbox):
    sid, fake_group, creator = sandbox
    return SandboxBot(sandbox_id=sid, fake_group_id=fake_group, creator_fake_user_id=creator)


@pytest.mark.asyncio
async def test_send_message_records_transcript_entry(bot, sandbox):
    sid, fake_group, _ = sandbox
    msg = await bot.send_message(fake_group, "hello", parse_mode="HTML")
    assert msg.message_id == 1
    assert msg.chat.id == fake_group
    assert msg.text == "hello"
    entries = await ts.range_(sid)
    assert len(entries) == 1
    e = entries[0]
    assert e.type == "send"
    assert e.scope == "group"
    assert e.chat_id == fake_group
    assert e.message_id == 1
    assert e.text == "hello"
    assert e.parse_mode == "HTML"


@pytest.mark.asyncio
async def test_send_message_to_user_id_scopes_as_dm(bot, sandbox):
    sid, _, _ = sandbox
    fake_user = alloc_user_id(session_seq=0, player_idx=3)
    await bot.send_message(fake_user, "your role is detective")
    entries = await ts.range_(sid)
    assert entries[0].scope == "dm"
    assert entries[0].target_user_id == fake_user


@pytest.mark.asyncio
async def test_send_message_increments_message_id(bot, sandbox):
    _sid, fake_group, _ = sandbox
    a = await bot.send_message(fake_group, "1")
    b = await bot.send_message(fake_group, "2")
    c = await bot.send_message(fake_group, "3")
    assert (a.message_id, b.message_id, c.message_id) == (1, 2, 3)


@pytest.mark.asyncio
async def test_edit_message_text_links_to_original(bot, sandbox):
    sid, fake_group, _ = sandbox
    sent = await bot.send_message(fake_group, "before")
    await bot.edit_message_text("after", chat_id=fake_group, message_id=sent.message_id)
    entries = await ts.range_(sid)
    assert len(entries) == 2
    edit = entries[1]
    assert edit.type == "edit"
    assert edit.ref_message_id == sent.message_id
    assert edit.text == "after"


@pytest.mark.asyncio
async def test_delete_message_records_delete(bot, sandbox):
    sid, fake_group, _ = sandbox
    sent = await bot.send_message(fake_group, "delete me")
    ok = await bot.delete_message(chat_id=fake_group, message_id=sent.message_id)
    assert ok is True
    entries = await ts.range_(sid)
    assert entries[-1].type == "delete"
    assert entries[-1].ref_message_id == sent.message_id


@pytest.mark.asyncio
async def test_send_animation_records_media(bot, sandbox):
    sid, fake_group, _ = sandbox
    msg = await bot.send_animation(fake_group, "file_id_xyz", caption="🌙 Night")
    # Caller may read .animation.file_id and gracefully handle None — verify
    # we don't crash and the caption survived.
    assert msg.caption == "🌙 Night"
    entry = (await ts.range_(sid))[0]
    assert entry.media["type"] == "animation"
    assert entry.media["caption"] == "🌙 Night"


@pytest.mark.asyncio
async def test_answer_callback_query_records_toast(bot, sandbox):
    sid, _, _ = sandbox
    await bot.answer_callback_query("cb-123", text="Voted!", show_alert=False)
    entries = await ts.range_(sid)
    assert entries[0].type == "toast"
    assert entries[0].text == "Voted!"
    assert entries[0].extra["callback_query_id"] == "cb-123"


@pytest.mark.asyncio
async def test_get_chat_member_returns_creator_for_creator(bot, sandbox):
    _, fake_group, creator = sandbox
    member = await bot.get_chat_member(fake_group, creator)
    assert member.status == "creator"


@pytest.mark.asyncio
async def test_get_chat_member_returns_member_for_others(bot, sandbox):
    _, fake_group, _ = sandbox
    other = alloc_user_id(session_seq=0, player_idx=5)
    member = await bot.get_chat_member(fake_group, other)
    assert member.status == "member"


@pytest.mark.asyncio
async def test_export_chat_invite_link_returns_fake_link(bot, sandbox):
    _, fake_group, _ = sandbox
    link = await bot.export_chat_invite_link(fake_group)
    assert link.startswith("https://t.me/")
    assert str(fake_group) in link


@pytest.mark.asyncio
async def test_pin_chat_message_records_pin(bot, sandbox):
    sid, fake_group, _ = sandbox
    sent = await bot.send_message(fake_group, "📌")
    await bot.pin_chat_message(fake_group, sent.message_id)
    entries = await ts.range_(sid)
    assert entries[-1].type == "pin"
    assert entries[-1].ref_message_id == sent.message_id


@pytest.mark.asyncio
async def test_serialize_keyboard_handles_aiogram_objects():
    """The serializer must accept anything with .inline_keyboard exposing
    button objects with .text/.callback_data attributes — that's the
    surface aiogram's InlineKeyboardMarkup provides."""

    class _Btn:
        def __init__(self, text, callback_data=None, url=None):
            self.text = text
            self.callback_data = callback_data
            self.url = url

    class _KB:
        def __init__(self, rows):
            self.inline_keyboard = rows

    kb = _KB(
        [
            [_Btn("Yes", "vote:yes"), _Btn("No", "vote:no")],
            [_Btn("Read more", url="https://example.com")],
        ]
    )
    out = _serialize_keyboard(kb)
    assert out == {
        "inline_keyboard": [
            [
                {"text": "Yes", "callback_data": "vote:yes"},
                {"text": "No", "callback_data": "vote:no"},
            ],
            [{"text": "Read more", "url": "https://example.com"}],
        ],
    }


def test_serialize_keyboard_handles_none():
    assert _serialize_keyboard(None) is None


def test_scope_for_classifies_correctly():
    fake_group = alloc_group_id(session_seq=0)
    fake_user = alloc_user_id(session_seq=0, player_idx=0)
    assert _scope_for(fake_group, fake_group) == "group"
    assert _scope_for(fake_user, fake_group) == "dm"
    # Other sandbox group id (e.g. a second concurrent session) → group scope
    other_group = alloc_group_id(session_seq=1)
    assert _scope_for(other_group, fake_group) == "group"


@pytest.mark.asyncio
async def test_registry_round_trip(bot, sandbox):
    _, fake_group, _ = sandbox
    SandboxBotRegistry.register(bot)
    assert SandboxBotRegistry.get(fake_group) is bot
    SandboxBotRegistry.unregister(fake_group)
    assert SandboxBotRegistry.get(fake_group) is None


@pytest.mark.asyncio
async def test_message_ids_are_per_sandbox():
    """Two concurrent sandboxes must not share their message_id counter."""
    sid_a, sid_b = uuid4(), uuid4()
    bot_a = SandboxBot(
        sandbox_id=sid_a, fake_group_id=alloc_group_id(0), creator_fake_user_id=alloc_user_id(0, 0)
    )
    bot_b = SandboxBot(
        sandbox_id=sid_b, fake_group_id=alloc_group_id(1), creator_fake_user_id=alloc_user_id(1, 0)
    )
    a = await bot_a.send_message(bot_a.fake_group_id, "hi")
    b = await bot_b.send_message(bot_b.fake_group_id, "hi")
    # Each starts at 1 — counters are keyed by sandbox_id.
    assert a.message_id == 1
    assert b.message_id == 1


@pytest.mark.asyncio
async def test_send_invoice_records_marker_entry(bot, sandbox):
    sid, _, _ = sandbox
    fake_user = alloc_user_id(session_seq=0, player_idx=1)
    await bot.send_invoice(
        fake_user,
        title="100 Diamonds",
        description="Buy 100 diamonds",
        prices=[{"label": "Stars", "amount": 100}],
    )
    entry = (await ts.range_(sid))[0]
    assert entry.media is not None and entry.media["type"] == "invoice"
    assert entry.text == "Buy 100 diamonds"
