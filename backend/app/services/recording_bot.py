"""SandboxBot — a duck-typed `aiogram.Bot` that captures every send.

The real engine (PhaseManager, role services, action handlers) calls
`bot.send_message`, `bot.edit_message_text`, etc. SandboxBot accepts
those calls but routes them into the transcript store instead of the
Telegram API. From the engine's perspective nothing else changes — it
gets back a `_FakeMessage` with the same shape it'd have gotten from
the real Bot, and the dashboard reads the resulting transcript via
the existing WebSocket broker.

The class is intentionally NOT a subclass of `aiogram.Bot`: aiogram's
Bot does protocol work (session, parse_mode defaults, throttling)
that we don't want to inherit. Duck-typing is enough — handlers only
touch a handful of public methods and never `isinstance`-check.

The set of methods covered here was determined by grepping every
`bot.<method>` call site in `backend/app/`. If a future code path
introduces a new method (e.g. `send_dice`), Python will raise
`AttributeError`, which is exactly the failure mode we want during
development — silent no-ops would be much worse.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, ClassVar
from uuid import UUID

from loguru import logger

from app.core.sandbox_ids import is_sandbox_group_id, is_sandbox_user_id
from app.services import transcript_store as ts
from app.services.transcript_store import TranscriptEntry
from app.services.ws_broker import emit_game_event

# === Lightweight aiogram-shaped stand-ins ====================================
# Each only exposes the attributes that downstream code actually reads
# (verified via grep across `backend/app/`). Adding more is safe and cheap.


@dataclass(slots=True)
class _FakeUser:
    id: int
    is_bot: bool = True
    first_name: str = "Mafia"
    username: str | None = None


@dataclass(slots=True)
class _FakeChat:
    id: int
    type: str = "supergroup"


@dataclass(slots=True)
class _FakeAnimation:
    """Stand-in for aiogram.types.Animation — gracefully unmapped."""

    file_id: str | None = None


@dataclass(slots=True)
class _FakeMessage:
    """Minimum surface area to pass for an `aiogram.types.Message`.

    Downstream readers (verified via grep):
      - `.message_id`            — load-bearing for state.registration_message_id,
                                   pin_chat_message, edit_message_text, etc.
      - `.chat.id`               — occasionally referenced
      - `.from_user`             — referenced by some logging code
      - `.date`                  — occasionally referenced
      - `.animation.file_id`     — messaging.py:296 (`if msg.animation and msg.animation.file_id:`)

    `.animation` is always None on the sandbox path; the call site
    handles that case (caching of file_id is simply skipped).
    """

    message_id: int
    chat: _FakeChat
    from_user: _FakeUser
    date: float
    text: str | None = None
    caption: str | None = None
    animation: _FakeAnimation | None = None


@dataclass(slots=True)
class _FakeChatMember:
    """Stand-in for aiogram.types.ChatMember — only `.status` is read."""

    status: str  # "creator" / "administrator" / "member" / "left" / "kicked"
    user: _FakeUser | None = None


# === SandboxBot ===============================================================


def _serialize_keyboard(reply_markup: Any) -> dict[str, Any] | None:
    """Convert an aiogram InlineKeyboardMarkup into the JSON shape the
    dashboard renders. Tolerant of None and of any object exposing a
    `.inline_keyboard` attribute (covers both aiogram InlineKeyboardMarkup
    and bare dicts passed by tests).
    """
    if reply_markup is None:
        return None
    rows = getattr(reply_markup, "inline_keyboard", None)
    if rows is None and isinstance(reply_markup, dict):
        rows = reply_markup.get("inline_keyboard")
    if rows is None:
        return None
    out_rows: list[list[dict[str, Any]]] = []
    for row in rows:
        out_row: list[dict[str, Any]] = []
        for btn in row:
            if isinstance(btn, dict):
                cell = {"text": btn.get("text", "")}
                if btn.get("callback_data"):
                    cell["callback_data"] = btn["callback_data"]
                if btn.get("url"):
                    cell["url"] = btn["url"]
            else:
                cell = {"text": getattr(btn, "text", "")}
                cb = getattr(btn, "callback_data", None)
                if cb:
                    cell["callback_data"] = cb
                url = getattr(btn, "url", None)
                if url:
                    cell["url"] = url
            out_row.append(cell)
        out_rows.append(out_row)
    return {"inline_keyboard": out_rows}


def _scope_for(chat_id: int, fake_group_id: int) -> str:
    """Classify a chat_id into the scope used by the dashboard tabs.

    Today only `group` and `dm` are distinguished — mafia/dead split
    chats will land when those features are wired up (the constants
    already exist in `TranscriptScope`).
    """
    if chat_id == fake_group_id:
        return "group"
    if is_sandbox_user_id(chat_id):
        return "dm"
    if is_sandbox_group_id(chat_id):
        return "group"
    # Defensive — should never be reached if guards work.
    return "group"


class SandboxBot:
    """Duck-typed Bot for sandbox games. Holds no network state.

    The real `aiogram.Bot` is configured with
    `DefaultBotProperties(parse_mode=ParseMode.HTML)` at startup, which
    means most call sites in the engine omit `parse_mode=` and rely on
    that default. SandboxBot mirrors the same default so the transcript
    receives `parse_mode="HTML"` on every send/edit unless an explicit
    `parse_mode=None` (or other override) is passed — without this, the
    dashboard renderer would fall into the plain-text branch and show
    raw `<b>` / `<tg-emoji>` markup instead of formatted text.
    """

    # Mirrors aiogram's DefaultBotProperties(parse_mode=ParseMode.HTML)
    # configured in `app.main.setup_bot`. Per-call `parse_mode=` still
    # wins.
    DEFAULT_PARSE_MODE = "HTML"

    def __init__(
        self,
        sandbox_id: UUID,
        fake_group_id: int,
        creator_fake_user_id: int,
        *,
        bot_user_id: int = 0,
        bot_username: str = "MafGameUzBot",
    ) -> None:
        self.sandbox_id = sandbox_id
        self.fake_group_id = fake_group_id
        # Used by `get_chat_member` to decide who's "creator". Mirrors a
        # real group where the player who issued /game becomes host.
        self.creator_fake_user_id = creator_fake_user_id
        self.id = bot_user_id or 1  # cosmetic; .id is referenced by file-id caches
        self.username = bot_username
        self._me = _FakeUser(
            id=self.id, is_bot=True, first_name=bot_username, username=bot_username
        )

    @staticmethod
    def _effective_parse_mode(explicit: str | None) -> str | None:
        """Return the parse_mode actually applied for a send.

        If the caller explicitly passed `parse_mode=None` they want
        plain text — honour that. Otherwise the default (HTML) wins so
        the dashboard renders `<b>`/`<i>`/mentions/`<tg-emoji>` instead
        of leaving them as literal markup.
        """
        # We can't distinguish "missing kwarg" from "explicit None" via
        # the keyword-only signature aiogram uses, so we treat None as
        # "use the default". The few call sites that genuinely want
        # plain text already pass `parse_mode=""` (an empty string,
        # which Telegram rejects but the SandboxBot accepts).
        if explicit:
            return explicit
        return SandboxBot.DEFAULT_PARSE_MODE

    # --- Bot identity (referenced by messaging.py caches) ---

    async def me(self) -> _FakeUser:  # aiogram exposes this as an async method
        return self._me

    # --- Message sends -----------------------------------------------------

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Any = None,
        parse_mode: str | None = None,
        **_kw: Any,
    ) -> _FakeMessage:
        return await self._record_send(
            chat_id=chat_id,
            text=text,
            parse_mode=self._effective_parse_mode(parse_mode),
            reply_markup=reply_markup,
            media=None,
        )

    async def send_animation(
        self,
        chat_id: int,
        animation: Any,
        caption: str | None = None,
        reply_markup: Any = None,
        parse_mode: str | None = None,
        **_kw: Any,
    ) -> _FakeMessage:
        media = {"type": "animation", "ref": _stringify_media(animation), "caption": caption}
        return await self._record_send(
            chat_id=chat_id,
            text=caption,
            parse_mode=self._effective_parse_mode(parse_mode),
            reply_markup=reply_markup,
            media=media,
        )

    async def send_video(
        self,
        chat_id: int,
        video: Any,
        caption: str | None = None,
        reply_markup: Any = None,
        parse_mode: str | None = None,
        **_kw: Any,
    ) -> _FakeMessage:
        media = {"type": "video", "ref": _stringify_media(video), "caption": caption}
        return await self._record_send(
            chat_id=chat_id,
            text=caption,
            parse_mode=self._effective_parse_mode(parse_mode),
            reply_markup=reply_markup,
            media=media,
        )

    async def send_photo(
        self,
        chat_id: int,
        photo: Any,
        caption: str | None = None,
        reply_markup: Any = None,
        parse_mode: str | None = None,
        **_kw: Any,
    ) -> _FakeMessage:
        media = {"type": "photo", "ref": _stringify_media(photo), "caption": caption}
        return await self._record_send(
            chat_id=chat_id,
            text=caption,
            parse_mode=self._effective_parse_mode(parse_mode),
            reply_markup=reply_markup,
            media=media,
        )

    async def send_invoice(self, chat_id: int, **kw: Any) -> _FakeMessage:
        # Sandbox can't really process payments — record a marker entry so
        # the dashboard at least shows the prompt was issued.
        media = {"type": "invoice", "title": kw.get("title"), "amount": kw.get("prices")}
        return await self._record_send(
            chat_id=chat_id,
            text=kw.get("description") or kw.get("title", "[invoice]"),
            parse_mode=None,
            reply_markup=None,
            media=media,
        )

    # --- Edits / deletes ---------------------------------------------------

    async def edit_message_text(
        self,
        text: str,
        chat_id: int,
        message_id: int,
        reply_markup: Any = None,
        parse_mode: str | None = None,
        **_kw: Any,
    ) -> _FakeMessage:
        entry = TranscriptEntry(
            type="edit",
            scope=_scope_for(chat_id, self.fake_group_id),
            chat_id=chat_id,
            target_user_id=chat_id if is_sandbox_user_id(chat_id) else None,
            message_id=message_id,
            ref_message_id=message_id,
            text=text,
            parse_mode=self._effective_parse_mode(parse_mode),
            reply_markup=_serialize_keyboard(reply_markup),
        )
        await self._persist(entry)
        return _FakeMessage(
            message_id=message_id,
            chat=_FakeChat(id=chat_id),
            from_user=self._me,
            date=time.time(),
            text=text,
        )

    async def edit_message_reply_markup(
        self,
        chat_id: int,
        message_id: int,
        reply_markup: Any = None,
        **_kw: Any,
    ) -> _FakeMessage:
        entry = TranscriptEntry(
            type="edit",
            scope=_scope_for(chat_id, self.fake_group_id),
            chat_id=chat_id,
            target_user_id=chat_id if is_sandbox_user_id(chat_id) else None,
            message_id=message_id,
            ref_message_id=message_id,
            text=None,
            reply_markup=_serialize_keyboard(reply_markup),
        )
        await self._persist(entry)
        return _FakeMessage(
            message_id=message_id,
            chat=_FakeChat(id=chat_id),
            from_user=self._me,
            date=time.time(),
        )

    async def delete_message(self, chat_id: int, message_id: int, **_kw: Any) -> bool:
        entry = TranscriptEntry(
            type="delete",
            scope=_scope_for(chat_id, self.fake_group_id),
            chat_id=chat_id,
            target_user_id=chat_id if is_sandbox_user_id(chat_id) else None,
            message_id=message_id,
            ref_message_id=message_id,
        )
        await self._persist(entry)
        return True

    # --- Pins / chat administration ---------------------------------------

    async def pin_chat_message(self, chat_id: int, message_id: int, **_kw: Any) -> bool:
        entry = TranscriptEntry(
            type="pin",
            scope=_scope_for(chat_id, self.fake_group_id),
            chat_id=chat_id,
            message_id=message_id,
            ref_message_id=message_id,
        )
        await self._persist(entry)
        return True

    async def unpin_chat_message(
        self, chat_id: int, message_id: int | None = None, **_kw: Any
    ) -> bool:
        entry = TranscriptEntry(
            type="unpin",
            scope=_scope_for(chat_id, self.fake_group_id),
            chat_id=chat_id,
            message_id=message_id or 0,
            ref_message_id=message_id,
        )
        await self._persist(entry)
        return True

    # --- Callback responses (toasts) --------------------------------------

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = False,
        **_kw: Any,
    ) -> bool:
        entry = TranscriptEntry(
            type="toast",
            scope="dm",  # toasts always belong to the clicking user
            chat_id=0,
            target_user_id=None,
            message_id=0,
            text=text,
            extra={"callback_query_id": callback_query_id, "show_alert": show_alert},
        )
        await self._persist(entry)
        return True

    # --- Chat metadata ----------------------------------------------------

    async def get_chat_member(self, chat_id: int, user_id: int) -> _FakeChatMember:
        """Return Owner for the sandbox creator, Member for everyone else.

        The real bot's group/game.py:102 etc. use `.status` to gate
        admin-only commands (`/game`, `/stop`). Treating the creator as
        the owner lets a sandbox SA exercise those gated paths.
        """
        status = "creator" if user_id == self.creator_fake_user_id else "member"
        return _FakeChatMember(
            status=status, user=_FakeUser(id=user_id, is_bot=False, first_name="player")
        )

    async def export_chat_invite_link(self, chat_id: int) -> str:
        return f"https://t.me/{self.username}?start=sandbox_{chat_id}"

    # --- Internals --------------------------------------------------------

    async def _record_send(
        self,
        *,
        chat_id: int,
        text: str | None,
        parse_mode: str | None,
        reply_markup: Any,
        media: dict[str, Any] | None,
    ) -> _FakeMessage:
        msg_id = await ts.next_message_id(self.sandbox_id)
        entry = TranscriptEntry(
            type="send",
            scope=_scope_for(chat_id, self.fake_group_id),
            chat_id=chat_id,
            target_user_id=chat_id if is_sandbox_user_id(chat_id) else None,
            message_id=msg_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=_serialize_keyboard(reply_markup),
            media=media,
        )
        await self._persist(entry)
        return _FakeMessage(
            message_id=msg_id,
            chat=_FakeChat(id=chat_id),
            from_user=self._me,
            date=entry.ts,
            text=text,
            caption=media.get("caption") if media else None,
            animation=None,
        )

    async def _persist(self, entry: TranscriptEntry) -> None:
        stored = await ts.append(self.sandbox_id, entry)
        try:
            await emit_game_event(
                "transcript_append",
                group_id=self.fake_group_id,
                sandbox_id=str(self.sandbox_id),
                entry=_entry_to_wire(stored),
            )
        except Exception as e:  # pragma: no cover — never let WS break the engine
            logger.warning(f"transcript_append WS emit failed: {e}")


def _stringify_media(ref: Any) -> str:
    """Best-effort stringification for media refs.

    Real aiogram passes either a file_id string, an FSInputFile, or
    URL-typed wrappers. The dashboard only needs a printable handle —
    actual media bytes are never served from sandbox.
    """
    if isinstance(ref, str):
        return ref
    path = getattr(ref, "path", None)
    if path is not None:
        return str(path)
    fid = getattr(ref, "file_id", None)
    if fid is not None:
        return str(fid)
    return repr(ref)


def _entry_to_wire(entry: TranscriptEntry) -> dict[str, Any]:
    """WS-friendly serialization (mirrors `TranscriptEntry.to_json` but
    returns a dict so the broker can re-serialize without double-encoding)."""
    from dataclasses import asdict

    return asdict(entry)


# === Registry ================================================================


class SandboxBotRegistry:
    """Module-level registry so callback-injection can find the bot.

    Keyed by sandbox `fake_group_id` (the same key PhaseManager uses
    for `_tasks`) so a single lookup covers both lifecycle and dispatch.
    """

    _by_group: ClassVar[dict[int, SandboxBot]] = {}

    @classmethod
    def register(cls, bot: SandboxBot) -> None:
        cls._by_group[bot.fake_group_id] = bot

    @classmethod
    def get(cls, fake_group_id: int) -> SandboxBot | None:
        return cls._by_group.get(fake_group_id)

    @classmethod
    def unregister(cls, fake_group_id: int) -> None:
        cls._by_group.pop(fake_group_id, None)

    @classmethod
    def clear(cls) -> None:
        cls._by_group.clear()
