"""Sandbox guards in stats / achievement / afk services must short-circuit."""

import pytest
from app.core.sandbox_ids import alloc_group_id, alloc_user_id
from app.core.state import GameState, Phase, PlayerState, Team
from app.services.achievement_service import check_and_unlock
from app.services.stats_service import finalize_game_stats


def _sandbox_state(group_id: int | None = None, winner: Team = Team.CITIZENS) -> GameState:
    if group_id is None:
        group_id = alloc_group_id(0)
    state = GameState(group_id=group_id, chat_id=group_id, phase=Phase.FINISHED)
    state.winner_team = winner
    state.players.append(
        PlayerState(
            user_id=alloc_user_id(0, 0),
            first_name="Player",
            join_order=1,
            role="citizen",
            team=Team.CITIZENS,
        )
    )
    return state


@pytest.mark.asyncio
async def test_finalize_game_stats_no_op_for_sandbox(monkeypatch):
    """finalize_game_stats must return immediately for sandbox — must not
    even touch Game.get_or_none (which would hit DB)."""
    db_touched: list[str] = []

    async def _fail(*a, **kw):
        db_touched.append("Game.get_or_none")
        raise AssertionError("sandbox path must not touch DB")

    monkeypatch.setattr("app.services.stats_service.Game.get_or_none", _fail)
    state = _sandbox_state()
    await finalize_game_stats(state)
    assert db_touched == []


@pytest.mark.asyncio
async def test_check_and_unlock_no_op_for_sandbox_user(monkeypatch):
    """Sandbox users have no UserStats row; achievement check must skip."""

    async def _fail(*a, **kw):
        raise AssertionError("sandbox path must not touch DB")

    monkeypatch.setattr("app.services.achievement_service.UserStats.get_or_none", _fail)

    class _FakeUser:
        def __init__(self, uid):
            self.id = uid

    state = _sandbox_state()
    user = _FakeUser(alloc_user_id(0, 0))
    out = await check_and_unlock(user, state)
    assert out == []


@pytest.mark.asyncio
async def test_check_and_unlock_no_op_for_sandbox_state_even_with_real_user(monkeypatch):
    """If the state is sandbox, even a real-looking user_id must be skipped —
    you can't earn achievements in a test sandbox."""

    async def _fail(*a, **kw):
        raise AssertionError("sandbox path must not touch DB")

    monkeypatch.setattr("app.services.achievement_service.UserStats.get_or_none", _fail)

    class _FakeUser:
        def __init__(self, uid):
            self.id = uid

    state = _sandbox_state()
    user = _FakeUser(7_300_000_000)  # real-looking id, sandbox state
    out = await check_and_unlock(user, state)
    assert out == []


@pytest.mark.asyncio
async def test_track_phase_inactivity_no_op_for_sandbox(monkeypatch):
    """afk_service must skip sandbox so the SA can dwell on the dashboard
    without bankrupting fake users."""
    from app.services import afk_service

    settings_touched: list[str] = []
    original = afk_service.track_phase_inactivity

    state = _sandbox_state()

    # Inject sentinel that would be tripped if execution continued past
    # the sandbox guard.
    async def _trip_after_guard(*a, **kw):
        settings_touched.append("real path hit")

    monkeypatch.setattr("app.services.afk_service._safe_send", _trip_after_guard)

    await original(bot=None, state=state, ended_phase=Phase.NIGHT)
    assert settings_touched == []
