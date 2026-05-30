"""REST surface for the super-admin sandbox feature.

Routes are JWT-gated via the same `get_current_admin` dependency the
rest of the admin panel uses; we additionally require the
`superadmin` role since sandboxes execute real engine code and could
mask production traffic if misused.

Endpoint set mirrors `sandbox_service`:

  POST   /api/sa/sandbox/games                — create + (optionally) start
  POST   /api/sa/sandbox/games/{sid}/start    — start a CREATED session
  POST   /api/sa/sandbox/games/{sid}/callback — inject a button click
  POST   /api/sa/sandbox/games/{sid}/advance  — manual phase advance
  POST   /api/sa/sandbox/games/{sid}/stop     — terminate; keep history
  POST   /api/sa/sandbox/games/{sid}/restart  — stop + create-fresh with same config
  DELETE /api/sa/sandbox/games/{sid}          — destroy + remove from list
  GET    /api/sa/sandbox/games                — list
  GET    /api/sa/sandbox/games/{sid}          — one (full + final_state)
  GET    /api/sa/sandbox/games/{sid}/state    — live GameState (proxies /admin/groups/{gid}/live)
  GET    /api/sa/sandbox/games/{sid}/transcript?since=&limit=
"""

from __future__ import annotations

import json
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, Field

from app.api.deps import require_role
from app.db.models import (
    AdminAccount,
    SandboxAutoPlayMode,
    SandboxSession,
    SandboxStatus,
    SandboxTimingPreset,
)
from app.services import game_service, sandbox_service, transcript_store
from app.services.sandbox_service import SandboxCreateConfig, SandboxError

router = APIRouter(prefix="/api/sa/sandbox", tags=["sandbox"])

_superadmin = require_role("superadmin")


# === Pydantic schemas =========================================================


class SandboxCreateRequest(BaseModel):
    n_players: int = Field(ge=4, le=30)
    language: Literal["uz", "ru", "en"] = "uz"
    mafia_ratio: Literal["low", "high"] = "low"
    auto_play_mode: SandboxAutoPlayMode = SandboxAutoPlayMode.PAUSED
    timing_preset: SandboxTimingPreset = SandboxTimingPreset.FAST
    roles_enabled: dict[str, bool] | None = None
    timings: dict[str, int] | None = None
    custom_names: list[str] = Field(default_factory=list)
    seed: int | None = None
    start_immediately: bool = False  # convenience: create + start in one call


class SandboxCallbackRequest(BaseModel):
    user_id: int  # the fake user we're "clicking as"
    callback_data: str
    message_id: int
    chat_id: int | None = None  # default: same as user_id (DM scope)


class SandboxMessageRequest(BaseModel):
    user_id: int  # the fake user we're "typing as"
    text: str = Field(min_length=1, max_length=4096)
    chat_id: int | None = None  # default: same as user_id (DM scope)


class _PlayerEntry(BaseModel):
    user_id: int
    first_name: str
    username: str | None
    language_code: str
    role: str | None
    team: str | None


class SandboxSummary(BaseModel):
    """Lightweight shape for list views."""

    sandbox_id: UUID
    fake_group_id: int
    status: SandboxStatus
    n_players: int
    auto_play_mode: SandboxAutoPlayMode
    timing_preset: SandboxTimingPreset
    created_at: str
    started_at: str | None
    finished_at: str | None
    winner_team: str | None
    transcript_summary: dict[str, int] | None


class SandboxDetail(SandboxSummary):
    settings_snapshot: dict[str, Any]
    fake_users_snapshot: list[_PlayerEntry]
    final_state: dict[str, Any] | None


class TranscriptPage(BaseModel):
    entries: list[dict[str, Any]]
    next_since: int


# === Helpers ==================================================================


def _to_summary(session: SandboxSession) -> SandboxSummary:
    return SandboxSummary(
        sandbox_id=session.id,
        fake_group_id=session.fake_group_id,
        status=session.status,
        n_players=session.n_players,
        auto_play_mode=session.auto_play_mode,
        timing_preset=session.timing_preset,
        created_at=session.created_at.isoformat() if session.created_at else "",
        started_at=session.started_at.isoformat() if session.started_at else None,
        finished_at=session.finished_at.isoformat() if session.finished_at else None,
        winner_team=session.winner_team,
        transcript_summary=session.transcript_summary,
    )


def _to_detail(session: SandboxSession) -> SandboxDetail:
    return SandboxDetail(
        **_to_summary(session).model_dump(),
        settings_snapshot=session.settings_snapshot or {},
        fake_users_snapshot=[_PlayerEntry(**u) for u in (session.fake_users_snapshot or [])],
        final_state=session.final_state,
    )


def _wrap_sandbox_error(e: SandboxError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# === Endpoints ================================================================


@router.post("/games", response_model=SandboxDetail)
async def create_sandbox_game(
    payload: SandboxCreateRequest,
    admin: AdminAccount = Depends(_superadmin),
) -> SandboxDetail:
    """Create a fresh sandbox. If `start_immediately=True`, also calls start."""
    config = SandboxCreateConfig(
        n_players=payload.n_players,
        language=payload.language,
        mafia_ratio=payload.mafia_ratio,
        auto_play_mode=payload.auto_play_mode,
        timing_preset=payload.timing_preset,
        roles_enabled=payload.roles_enabled,
        timings=payload.timings,
        custom_names=payload.custom_names,
        seed=payload.seed,
    )
    try:
        session = await sandbox_service.create_sandbox(admin, config)
        if payload.start_immediately:
            session = await sandbox_service.start_sandbox(session.id)
    except SandboxError as e:
        raise _wrap_sandbox_error(e) from e
    return _to_detail(session)


@router.post("/games/{sandbox_id}/start", response_model=SandboxDetail)
async def start_sandbox_game(
    sandbox_id: UUID, admin: AdminAccount = Depends(_superadmin)
) -> SandboxDetail:
    try:
        session = await sandbox_service.start_sandbox(sandbox_id)
    except SandboxError as e:
        raise _wrap_sandbox_error(e) from e
    return _to_detail(session)


@router.post("/games/{sandbox_id}/callback")
async def post_callback(
    sandbox_id: UUID,
    payload: SandboxCallbackRequest,
    admin: AdminAccount = Depends(_superadmin),
) -> dict[str, bool]:
    """Dashboard button click → synthetic CallbackQuery → engine handler."""
    try:
        await sandbox_service.inject_callback(
            sandbox_id=sandbox_id,
            fake_user_id=payload.user_id,
            callback_data=payload.callback_data,
            message_id=payload.message_id,
            chat_id=payload.chat_id,
        )
    except SandboxError as e:
        raise _wrap_sandbox_error(e) from e
    except Exception as e:
        logger.exception(f"callback injection failed for sandbox {sandbox_id}: {e}")
        raise HTTPException(status_code=500, detail=f"callback failed: {e}") from e
    return {"ok": True}


@router.post("/games/{sandbox_id}/message")
async def post_message(
    sandbox_id: UUID,
    payload: SandboxMessageRequest,
    admin: AdminAccount = Depends(_superadmin),
) -> dict[str, bool]:
    """Dashboard text-input → synthetic Message → engine handler.

    Lets the operator type as a fake player, exercising mafia-chat
    relay, last-words capture, and anything else the private-chat
    text handlers act on.
    """
    try:
        await sandbox_service.inject_message(
            sandbox_id=sandbox_id,
            fake_user_id=payload.user_id,
            text=payload.text,
            chat_id=payload.chat_id,
        )
    except SandboxError as e:
        raise _wrap_sandbox_error(e) from e
    except Exception as e:
        logger.exception(f"message injection failed for sandbox {sandbox_id}: {e}")
        raise HTTPException(status_code=500, detail=f"message failed: {e}") from e
    return {"ok": True}


@router.post("/games/{sandbox_id}/advance")
async def advance_sandbox_phase(
    sandbox_id: UUID, admin: AdminAccount = Depends(_superadmin)
) -> dict[str, Any]:
    """Manual phase advance (manual_mode or operator click)."""
    try:
        phase = await sandbox_service.advance_phase(sandbox_id)
    except SandboxError as e:
        raise _wrap_sandbox_error(e) from e
    return {"phase": phase.value if phase else None}


@router.post("/games/{sandbox_id}/stop", response_model=SandboxDetail)
async def stop_sandbox_game(
    sandbox_id: UUID, admin: AdminAccount = Depends(_superadmin)
) -> SandboxDetail:
    try:
        session = await sandbox_service.stop_sandbox(sandbox_id)
    except SandboxError as e:
        raise _wrap_sandbox_error(e) from e
    return _to_detail(session)


@router.post("/games/{sandbox_id}/restart", response_model=SandboxDetail)
async def restart_sandbox_game(
    sandbox_id: UUID, admin: AdminAccount = Depends(_superadmin)
) -> SandboxDetail:
    """Stops the current session + creates a NEW one with the same config.

    Returns the new SandboxDetail. The old session row stays around in
    DESTROYED status so its transcript remains browsable.
    """
    try:
        new_session = await sandbox_service.restart_sandbox(sandbox_id)
    except SandboxError as e:
        raise _wrap_sandbox_error(e) from e
    return _to_detail(new_session)


@router.delete("/games/{sandbox_id}")
async def destroy_sandbox_game(
    sandbox_id: UUID, admin: AdminAccount = Depends(_superadmin)
) -> dict[str, bool]:
    """Stop + permanently remove the session row from the dashboard list."""
    try:
        await sandbox_service.destroy_sandbox(sandbox_id)
    except SandboxError as e:
        raise _wrap_sandbox_error(e) from e
    return {"ok": True}


@router.get("/games", response_model=list[SandboxSummary])
async def list_sandbox_games(
    admin: AdminAccount = Depends(_superadmin),
    status_filter: Literal["active", "all", "finished"] = Query("all", alias="status"),
    limit: int = Query(50, ge=1, le=200),
) -> list[SandboxSummary]:
    qs = SandboxSession.all().order_by("-created_at").limit(limit)
    if status_filter == "active":
        qs = qs.filter(status__in=[SandboxStatus.CREATED, SandboxStatus.RUNNING])
    elif status_filter == "finished":
        qs = qs.filter(status__in=[SandboxStatus.FINISHED, SandboxStatus.DESTROYED])
    sessions = await qs
    return [_to_summary(s) for s in sessions]


@router.get("/games/{sandbox_id}", response_model=SandboxDetail)
async def get_sandbox_game(
    sandbox_id: UUID, admin: AdminAccount = Depends(_superadmin)
) -> SandboxDetail:
    session = await SandboxSession.get_or_none(id=sandbox_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return _to_detail(session)


@router.get("/games/{sandbox_id}/state")
async def get_sandbox_state(
    sandbox_id: UUID, admin: AdminAccount = Depends(_superadmin)
) -> dict[str, Any]:
    """Live GameState — mirrors the shape of `/api/admin/groups/{gid}/live`.

    For sandboxes in `CREATED` or `RUNNING` the state is in Redis; for
    `FINISHED`/`DESTROYED` we return `final_state` from the DB row.
    """
    session = await SandboxSession.get_or_none(id=sandbox_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    state = await game_service.load_state(session.fake_group_id)
    if state is not None:
        return json.loads(state.to_redis())
    if session.final_state:
        return session.final_state
    raise HTTPException(status_code=404, detail="No state — sandbox not yet started")


@router.get("/games/{sandbox_id}/transcript", response_model=TranscriptPage)
async def get_sandbox_transcript(
    sandbox_id: UUID,
    admin: AdminAccount = Depends(_superadmin),
    since: int = Query(0, ge=0, description="Only return entries with seq > since"),
    limit: int = Query(200, ge=1, le=1000),
) -> TranscriptPage:
    """Paginated transcript fetch.

    For RUNNING sessions this reads the live Redis stream — clients
    should subscribe to the `transcript_append` WS event for deltas and
    fall back to this endpoint only on reconnect (to fill gaps).
    """
    session = await SandboxSession.get_or_none(id=sandbox_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    # Live Redis stream first; DB fallback for terminated sandboxes.
    entries = await transcript_store.range_(sandbox_id, since_seq=since, limit=limit)
    if not entries and session.status in (
        SandboxStatus.FINISHED,
        SandboxStatus.DESTROYED,
    ):
        from app.db.models import SandboxTranscriptEntry

        rows = (
            await SandboxTranscriptEntry.filter(session_id=sandbox_id, seq__gt=since)
            .order_by("seq")
            .limit(limit)
        )
        out_dicts = [
            {
                "seq": r.seq,
                "ts": r.ts.timestamp() if r.ts else 0.0,
                "type": r.type.value,
                "scope": r.scope.value,
                "chat_id": r.chat_id,
                "target_user_id": r.target_user_id,
                "message_id": r.message_id,
                "ref_message_id": r.ref_message_id,
                "text": r.text,
                "parse_mode": r.parse_mode,
                "reply_markup": r.reply_markup,
                "media": r.media,
                "extra": {},
            }
            for r in rows
        ]
        next_since = out_dicts[-1]["seq"] if out_dicts else since
        return TranscriptPage(entries=out_dicts, next_since=next_since)

    from dataclasses import asdict

    out = [asdict(e) for e in entries]
    next_since = out[-1]["seq"] if out else since
    return TranscriptPage(entries=out, next_since=next_since)
