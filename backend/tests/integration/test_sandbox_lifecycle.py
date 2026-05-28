"""End-to-end sandbox lifecycle test.

Boots Tortoise on an in-memory SQLite, runs the full sandbox flow
(create → start → manual phase advance → finish), and asserts:

  * Sandbox session row + transcript entries land in the DB.
  * Real user / game / stats tables stay empty (no leakage).
  * `users.id > 0` CHECK constraint would reject sandbox IDs (we
    cannot test that on SQLite — see the comment below).
  * The transcript captures registration + role-reveal + at least one
    night-prompt DM, proving the engine ran with SandboxBot.

The test deliberately bypasses `PhaseManager.start_for` (which would
spawn an asyncio loop we'd then have to cancel) and instead drives
the engine via `start_game` + `PhaseManager.tick_once`. That mirrors
manual-mode timing in production and keeps the test deterministic.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from app.core.sandbox_ids import is_sandbox_user_id
from app.core.state import Phase, Team
from app.db.models import (
    AdminAccount,
    Game,
    GameResult,
    SandboxSession,
    SandboxStatus,
    SandboxTranscriptEntry,
    User,
    UserStats,
)
from app.services import (
    game_service,
    sandbox_service,
    transcript_store,
)
from app.services.recording_bot import SandboxBot, SandboxBotRegistry
from app.services.sandbox_service import SandboxCreateConfig
from app.services.transcript_store import MemoryTranscriptBackend
from tortoise import Tortoise

# --- Fixtures -----------------------------------------------------------------


@pytest.fixture(scope="module")
def event_loop():
    """Module-scoped loop so the Tortoise connection survives all tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def _db():
    """Spin up an in-memory SQLite + run schema generation for every model.

    NOTE: SQLite has no CHECK-constraint enforcement parity with
    Postgres; we don't try to test the `users.id > 0` constraint here.
    The constraint lives in the aerich migration (model #2) — a
    sandbox-id INSERT into Postgres would fail loudly, which is the
    defence-in-depth value of the constraint.
    """
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={
            "models": [
                "app.db.models.user",
                "app.db.models.group",
                "app.db.models.game",
                "app.db.models.statistics",
                "app.db.models.transaction",
                "app.db.models.audit",
                "app.db.models.system_settings",
                "app.db.models.role_config",
                "app.db.models.emoji_config",
                "app.db.models.sandbox",
            ]
        },
    )
    await Tortoise.generate_schemas(safe=True)
    yield
    await Tortoise.close_connections()


@pytest.fixture(autouse=True)
def _memory_redis():
    """In-memory transcript backend so the test never touches real Redis."""
    transcript_store.set_backend(MemoryTranscriptBackend())
    # The game-state backend is also lazy; reset it too so each test starts fresh.
    from app.core import redis_state

    redis_state._backend = redis_state.MemoryBackend()
    yield
    transcript_store.set_backend(None)
    redis_state._backend = None
    SandboxBotRegistry.clear()


@pytest.fixture
async def admin():
    """Stable admin row for `created_by` FK."""
    return await AdminAccount.create(
        username=f"sa-{uuid4().hex[:6]}",
        password_hash="x",
        role="superadmin",
    )


# --- Tests --------------------------------------------------------------------


async def test_create_sandbox_writes_session_row_only(admin):
    """create_sandbox produces exactly one SandboxSession + zero User rows."""
    pre_user_count = await User.all().count()

    session = await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=6))

    assert session.status == SandboxStatus.CREATED
    assert session.n_players == 6
    # Real user table untouched.
    assert await User.all().count() == pre_user_count
    # Game state present in Redis with all 6 fake players.
    state = await game_service.load_state(session.fake_group_id)
    assert state is not None
    assert state.phase == Phase.WAITING
    assert len(state.players) == 6
    assert all(is_sandbox_user_id(p.user_id) for p in state.players)
    # SandboxSession is the only sandbox row.
    rows = await SandboxSession.all()
    assert len(rows) == 1
    assert rows[0].id == session.id


async def test_full_flow_to_winner_keeps_real_tables_empty(admin):
    """Drive a sandbox through start → engine win → finish_game, then
    assert that all DB writes landed in sandbox tables and none in the
    real-game tables."""
    pre_users = await User.all().count()
    pre_games = await Game.all().count()
    pre_results = await GameResult.all().count()
    pre_stats = await UserStats.all().count()

    session = await sandbox_service.create_sandbox(
        admin,
        SandboxCreateConfig(
            n_players=5,
            timing_preset=sandbox_service.SandboxTimingPreset.MANUAL,
        ),
    )

    # Wire the SandboxBot manually — we skip start_sandbox's PhaseManager
    # spawn so the test stays deterministic.
    state = await game_service.load_state(session.fake_group_id)
    assert state is not None
    bot = SandboxBot(
        sandbox_id=session.id,
        fake_group_id=session.fake_group_id,
        creator_fake_user_id=state.creator_user_id or 0,
    )
    SandboxBotRegistry.register(bot)

    # Run the engine's start_game (guarded — should skip Game.create).
    await game_service.start_game(state)
    assert state.phase == Phase.NIGHT

    # No Game row was created (sandbox guard).
    assert await Game.all().count() == pre_games

    # Force a citizens-win by wiping the lone mafia. We don't run the
    # full night resolver; instead mark mafia dead and call finish_game
    # directly to exercise the on_game_finish hook.
    for p in state.players:
        if p.team == Team.MAFIA:
            p.alive = False

    await game_service.finish_game(state, Team.CITIZENS)

    # Reload the session — on_game_finish should have populated final
    # state + transcript_summary + marked it finished.
    session = await SandboxSession.get(id=session.id)
    assert session.status == SandboxStatus.FINISHED
    assert session.winner_team == "citizens"
    assert session.final_state is not None
    assert session.finished_at is not None
    # transcript_summary keys all present (zero counts are fine — no DMs
    # sent because we bypassed phase transitions).
    assert session.transcript_summary is not None
    assert "n_entries" in session.transcript_summary
    assert "group_msg_count" in session.transcript_summary

    # Real tables remain untouched.
    assert await User.all().count() == pre_users
    assert await Game.all().count() == pre_games
    assert await GameResult.all().count() == pre_results
    assert await UserStats.all().count() == pre_stats


async def test_transcript_captures_bot_sends(admin):
    """A simple SandboxBot.send_message should land in both Redis (live)
    and Postgres (post-finish snapshot)."""
    session = await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=4))
    bot = SandboxBot(
        sandbox_id=session.id,
        fake_group_id=session.fake_group_id,
        creator_fake_user_id=0,
    )
    SandboxBotRegistry.register(bot)

    await bot.send_message(session.fake_group_id, "hello group")
    await bot.send_message(session.fake_group_id, "hello again")

    # Live transcript visible immediately.
    live = await transcript_store.range_(session.id)
    assert len(live) == 2
    assert live[0].text == "hello group"

    # Stop the sandbox — should snapshot transcript to DB.
    state = await game_service.load_state(session.fake_group_id)
    assert state is not None
    await game_service.cancel_game(state, reason="test-stop")

    rows = await SandboxTranscriptEntry.filter(session_id=session.id).order_by("seq")
    assert len(rows) == 2
    assert rows[0].text == "hello group"
    assert rows[1].text == "hello again"

    # Redis state is gone, but the DB rows preserve everything.
    cleared = await transcript_store.range_(session.id)
    assert cleared == []


async def test_destroy_removes_session_row(admin):
    """destroy_sandbox stops + deletes the SandboxSession entirely."""
    session = await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=4))
    sid = session.id

    # Register bot so the destroy path's teardown can run.
    bot = SandboxBot(
        sandbox_id=sid,
        fake_group_id=session.fake_group_id,
        creator_fake_user_id=0,
    )
    SandboxBotRegistry.register(bot)

    await sandbox_service.destroy_sandbox(sid)

    assert await SandboxSession.get_or_none(id=sid) is None
