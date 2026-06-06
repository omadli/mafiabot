"""Unit tests for sandbox_service.

Tests cover the pure logic + the Redis-side of `create_sandbox` (state +
fake users + transcript meta). DB-touching paths (`SandboxSession.create`,
`start_sandbox` → full engine) are exercised in the integration suite —
`tests/integration/test_sandbox_lifecycle.py` (task #14).
"""

from uuid import UUID, uuid4

import pytest
from app.core.sandbox_ids import (
    GROUP_RANGE_START,
    USER_RANGE_START,
    is_sandbox_group_id,
    is_sandbox_user_id,
)
from app.core.state import Phase
from app.db.models import SandboxAutoPlayMode, SandboxStatus, SandboxTimingPreset
from app.services import game_service, sandbox_service, transcript_store
from app.services.recording_bot import SandboxBotRegistry
from app.services.sandbox_service import (
    _FAKE_NAMES,
    _TIMING_PRESETS,
    SandboxCreateConfig,
    SandboxError,
    _settings_snapshot,
)

# === Pure logic ===============================================================


def test_timing_preset_keys_match_default():
    """All presets cover the same set of timing keys as DEFAULT_TIMINGS."""
    from app.db.models.group import DEFAULT_TIMINGS

    for preset_name, preset in _TIMING_PRESETS.items():
        assert preset.keys() == DEFAULT_TIMINGS.keys(), (
            f"preset {preset_name} keys diverged from DEFAULT_TIMINGS"
        )


def test_fast_preset_is_faster_than_normal():
    fast = _TIMING_PRESETS["fast"]
    normal = _TIMING_PRESETS["normal"]
    assert fast["night"] < normal["night"]
    assert fast["day"] < normal["day"]
    assert fast["registration"] < normal["registration"]


def test_slow_preset_is_2x_normal():
    slow = _TIMING_PRESETS["slow"]
    normal = _TIMING_PRESETS["normal"]
    for k, v in normal.items():
        assert slow[k] == v * 2


def test_manual_preset_disables_auto_advance():
    """Manual mode must use very large timeouts so the PhaseManager
    only advances when explicitly told to."""
    manual = _TIMING_PRESETS["manual"]
    for v in manual.values():
        assert v >= 10**8  # effectively infinite


def test_settings_snapshot_uses_preset_timings():
    config = SandboxCreateConfig(n_players=8, timing_preset=SandboxTimingPreset.FAST)
    snap = _settings_snapshot(config)
    assert snap["timings"] == _TIMING_PRESETS["fast"]


def test_settings_snapshot_explicit_timings_override_preset():
    custom = {
        "night": 7,
        "day": 3,
        "registration": 2,
        "mafia_vote": 5,
        "hanging_vote": 5,
        "hanging_confirm": 5,
        "last_words": 5,
        "afsungar_carry": 5,
    }
    config = SandboxCreateConfig(
        n_players=8, timing_preset=SandboxTimingPreset.SLOW, timings=custom
    )
    snap = _settings_snapshot(config)
    assert snap["timings"] == custom


def test_settings_snapshot_roles_enabled_override_merges():
    config = SandboxCreateConfig(n_players=8, roles_enabled={"maniac": True, "killer": True})
    snap = _settings_snapshot(config)
    assert snap["roles"]["maniac"] is True
    assert snap["roles"]["killer"] is True
    # Other defaults preserved
    assert snap["roles"]["don"] is True


def test_settings_snapshot_carries_mafia_ratio():
    config = SandboxCreateConfig(n_players=8, mafia_ratio="high")
    snap = _settings_snapshot(config)
    assert snap["gameplay"]["mafia_ratio"] == "high"


def test_settings_snapshot_carries_language():
    snap = _settings_snapshot(SandboxCreateConfig(n_players=8, language="ru"))
    assert snap["language"] == "ru"


def test_fake_names_unique_within_default_set():
    assert len(set(_FAKE_NAMES)) == len(_FAKE_NAMES)
    # Enough names for the max sandbox size without cycling.
    assert len(_FAKE_NAMES) >= 30


# === create_sandbox =========================================================
#
# We stub `SandboxSession.create` so tests don't need a DB connection,
# and we set the transcript backend to in-memory so Redis isn't needed
# either. These tests verify the Redis-side wiring + GameState shape.


@pytest.fixture(autouse=True)
def memory_backends():
    """Inject in-memory backends for both transcript + game state."""
    from app.core import redis_state
    from app.services.transcript_store import MemoryTranscriptBackend

    transcript_store.set_backend(MemoryTranscriptBackend())

    # Reset the lazy game-state backend to a fresh memory instance.
    redis_state._backend = redis_state.MemoryBackend()

    yield

    transcript_store.set_backend(None)
    redis_state._backend = None
    SandboxBotRegistry.clear()


@pytest.fixture
def stub_session(monkeypatch):
    """Patch SandboxSession.create / .all to skip the DB.

    Returns a list that captures every SandboxSession-like dict the
    service tried to persist, so tests can assert against it.
    """
    persisted: list[dict] = []
    seq_counter = {"n": 0}

    class _StubSession:
        def __init__(self, **kw):
            self.id: UUID = uuid4()
            self.created_by_id = kw.get("created_by").id if kw.get("created_by") else None
            self.fake_group_id = kw.get("fake_group_id")
            self.n_players = kw.get("n_players")
            self.auto_play_mode = kw.get("auto_play_mode")
            self.timing_preset = kw.get("timing_preset")
            self.settings_snapshot = kw.get("settings_snapshot")
            self.fake_users_snapshot = kw.get("fake_users_snapshot")
            self.status = kw.get("status")
            self.started_at = None
            self.finished_at = None
            persisted.append({"kw": kw, "obj": self})

        async def save(self, update_fields=None):
            return None

    class _StubQuery:
        async def count(self):
            return seq_counter["n"]

    async def _create(**kw):
        s = _StubSession(**kw)
        seq_counter["n"] += 1
        return s

    monkeypatch.setattr(
        "app.services.sandbox_service.SandboxSession",
        type("_M", (), {"create": staticmethod(_create), "all": staticmethod(_StubQuery)}),
    )
    return persisted


@pytest.fixture
def admin():
    """Cheap admin stand-in — only .id is read by create_sandbox."""

    class _A:
        def __init__(self):
            self.id = uuid4()

    return _A()


@pytest.mark.asyncio
async def test_create_sandbox_rejects_invalid_player_count(admin):
    with pytest.raises(SandboxError, match="n_players"):
        await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=2))
    with pytest.raises(SandboxError, match="n_players"):
        await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=31))


@pytest.mark.asyncio
async def test_create_sandbox_allocates_fake_ids(admin, stub_session):
    session = await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=8))
    assert is_sandbox_group_id(session.fake_group_id)
    # First call → session_seq=0 → fake_group_id at range start
    assert session.fake_group_id == GROUP_RANGE_START
    # Players appear in Redis state with sandbox user IDs.
    state = await game_service.load_state(session.fake_group_id)
    assert state is not None
    assert state.phase == Phase.WAITING
    assert len(state.players) == 8
    for p in state.players:
        assert is_sandbox_user_id(p.user_id)
    # Player IDs are contiguous from USER_RANGE_START
    uids = sorted(p.user_id for p in state.players)
    assert uids[0] == USER_RANGE_START
    assert uids[-1] == USER_RANGE_START + 7


@pytest.mark.asyncio
async def test_create_sandbox_persists_fake_users_to_redis(admin, stub_session):
    session = await sandbox_service.create_sandbox(
        admin, SandboxCreateConfig(n_players=5, language="ru")
    )
    fakes = await transcript_store.list_fake_users(session.id)
    assert len(fakes) == 5
    assert all(u.language_code == "ru" for u in fakes)
    # Round-trip a single user
    state = await game_service.load_state(session.fake_group_id)
    sample_uid = state.players[2].user_id
    one = await transcript_store.get_fake_user(session.id, sample_uid)
    assert one is not None
    assert one.first_name == state.players[2].first_name


@pytest.mark.asyncio
async def test_create_sandbox_stores_meta(admin, stub_session):
    session = await sandbox_service.create_sandbox(
        admin,
        SandboxCreateConfig(
            n_players=6,
            auto_play_mode=SandboxAutoPlayMode.AUTO,
            timing_preset=SandboxTimingPreset.NORMAL,
        ),
    )
    meta = await transcript_store.get_meta(session.id)
    assert meta is not None
    assert meta["fake_group_id"] == session.fake_group_id
    assert meta["sandbox_id"] == str(session.id)
    assert meta["auto_play_mode"] == "auto"
    assert meta["timing_preset"] == "normal"
    assert meta["n_players"] == 6


@pytest.mark.asyncio
async def test_create_sandbox_uses_custom_names_when_supplied(admin, stub_session):
    names = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"]
    session = await sandbox_service.create_sandbox(
        admin,
        SandboxCreateConfig(n_players=5, custom_names=names),
    )
    state = await game_service.load_state(session.fake_group_id)
    assert [p.first_name for p in state.players] == names


@pytest.mark.asyncio
async def test_create_sandbox_falls_back_to_default_names(admin, stub_session):
    # n_players > custom_names → leftovers use _FAKE_NAMES.
    custom = ["Alpha", "Bravo"]
    session = await sandbox_service.create_sandbox(
        admin, SandboxCreateConfig(n_players=5, custom_names=custom)
    )
    state = await game_service.load_state(session.fake_group_id)
    assert state.players[0].first_name == "Alpha"
    assert state.players[1].first_name == "Bravo"
    # Remaining come from default pool.
    for p in state.players[2:]:
        assert p.first_name in _FAKE_NAMES


@pytest.mark.asyncio
async def test_create_sandbox_state_creator_is_first_player(admin, stub_session):
    session = await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=4))
    state = await game_service.load_state(session.fake_group_id)
    assert state.creator_user_id == state.players[0].user_id


@pytest.mark.asyncio
async def test_create_sandbox_settings_snapshot_captured_on_session_row(admin, stub_session):
    await sandbox_service.create_sandbox(
        admin,
        SandboxCreateConfig(
            n_players=4,
            roles_enabled={"maniac": True},
            mafia_ratio="high",
        ),
    )
    last = stub_session[-1]["kw"]
    assert last["settings_snapshot"]["roles"]["maniac"] is True
    assert last["settings_snapshot"]["gameplay"]["mafia_ratio"] == "high"
    assert last["status"] == SandboxStatus.CREATED


@pytest.mark.asyncio
async def test_create_sandbox_concurrent_sessions_get_disjoint_ids(admin, stub_session):
    s1 = await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=4))
    s2 = await sandbox_service.create_sandbox(admin, SandboxCreateConfig(n_players=4))
    assert s1.fake_group_id != s2.fake_group_id
    state1 = await game_service.load_state(s1.fake_group_id)
    state2 = await game_service.load_state(s2.fake_group_id)
    uids1 = {p.user_id for p in state1.players}
    uids2 = {p.user_id for p in state2.players}
    assert uids1.isdisjoint(uids2)
