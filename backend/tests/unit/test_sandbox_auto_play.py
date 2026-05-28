"""Tests for sandbox auto-play strategy.

The async background loop is exercised in the integration tests; here
we focus on the pure picker logic so it's fast + easy to read.
"""

import random

import pytest
from app.core.sandbox_ids import alloc_group_id, alloc_user_id
from app.core.state import GameState, NightAction, Phase, PlayerState, Team, Vote
from app.db.models import SandboxAutoPlayMode
from app.services.sandbox_service import (
    _pick_night_target,
    _pick_vote_target,
    _submit_auto_actions,
)


def _make_state(*roles_with_teams: tuple[str, Team], group_id: int | None = None) -> GameState:
    if group_id is None:
        group_id = alloc_group_id(0)
    state = GameState(group_id=group_id, chat_id=group_id, phase=Phase.NIGHT, round_num=1)
    for i, (role, team) in enumerate(roles_with_teams):
        state.players.append(
            PlayerState(
                user_id=alloc_user_id(0, i),
                first_name=f"P{i}",
                join_order=i + 1,
                role=role,
                team=team,
            )
        )
    return state


@pytest.fixture(autouse=True)
def deterministic():
    random.seed(42)


# --- Night target picking ----------------------------------------------------


def test_doctor_avoids_self_in_auto_mode():
    from app.core.roles import get_role

    state = _make_state(
        ("doctor", Team.CITIZENS),
        ("citizen", Team.CITIZENS),
        ("don", Team.MAFIA),
    )
    actor = state.players[0]
    role = get_role("doctor")
    # Run many trials — the doctor should never pick herself.
    for _ in range(50):
        target = _pick_night_target(role, actor, state, SandboxAutoPlayMode.AUTO.value)
        assert target is not None
        assert target.user_id != actor.user_id


def test_killing_roles_prefer_non_team_in_auto():
    from app.core.roles import get_role

    state = _make_state(
        ("don", Team.MAFIA),
        ("mafia", Team.MAFIA),
        ("citizen", Team.CITIZENS),
        ("detective", Team.CITIZENS),
    )
    actor = state.players[0]  # Don
    role = get_role("don")
    hits_non_mafia = 0
    trials = 50
    for _ in range(trials):
        target = _pick_night_target(role, actor, state, SandboxAutoPlayMode.AUTO.value)
        assert target is not None
        if target.team != Team.MAFIA:
            hits_non_mafia += 1
    # Auto mode should pick non-mafia *every* time when available.
    assert hits_non_mafia == trials


def test_detective_prefers_non_citizens_in_auto():
    from app.core.roles import get_role

    state = _make_state(
        ("detective", Team.CITIZENS),
        ("citizen", Team.CITIZENS),
        ("citizen", Team.CITIZENS),
        ("don", Team.MAFIA),
        ("maniac", Team.SINGLETON),
    )
    actor = state.players[0]
    role = get_role("detective")
    hits_suspect = 0
    trials = 50
    for _ in range(trials):
        target = _pick_night_target(role, actor, state, SandboxAutoPlayMode.AUTO.value)
        assert target is not None
        if target.team != Team.CITIZENS:
            hits_suspect += 1
    assert hits_suspect == trials


def test_random_mode_picks_any_valid_target():
    """Maniac's can_target is "any alive ≠ self", so random mode must hit
    multiple targets across many trials (vs auto mode which would still
    apply strategy filters)."""
    from app.core.roles import get_role

    state = _make_state(
        ("maniac", Team.SINGLETON),
        ("citizen", Team.CITIZENS),
        ("don", Team.MAFIA),
        ("doctor", Team.CITIZENS),
    )
    actor = state.players[0]  # Maniac — can target anyone alive ≠ self
    role = get_role("maniac")
    targets_seen = set()
    for _ in range(80):
        t = _pick_night_target(role, actor, state, SandboxAutoPlayMode.RANDOM_ACTIONS.value)
        if t:
            targets_seen.add(t.user_id)
    # All 3 non-self players are valid → random mode must hit all of them.
    assert len(targets_seen) == 3


# --- Vote picking -----------------------------------------------------------


def test_vote_picker_avoids_self():
    state = _make_state(
        ("citizen", Team.CITIZENS),
        ("citizen", Team.CITIZENS),
        ("don", Team.MAFIA),
    )
    voter = state.players[0]
    for _ in range(50):
        t = _pick_vote_target(voter, state, SandboxAutoPlayMode.AUTO.value)
        assert t is not None
        assert t.user_id != voter.user_id


def test_mafia_votes_lynch_non_mafia_in_auto():
    state = _make_state(
        ("don", Team.MAFIA),
        ("mafia", Team.MAFIA),
        ("citizen", Team.CITIZENS),
        ("detective", Team.CITIZENS),
    )
    don = state.players[0]
    for _ in range(50):
        t = _pick_vote_target(don, state, SandboxAutoPlayMode.AUTO.value)
        assert t is not None and t.team != Team.MAFIA


def test_voting_with_only_one_alive_returns_none():
    state = _make_state(("citizen", Team.CITIZENS))
    only = state.players[0]
    t = _pick_vote_target(only, state, SandboxAutoPlayMode.AUTO.value)
    assert t is None


# --- _submit_auto_actions end-to-end ----------------------------------------


@pytest.mark.asyncio
async def test_submit_night_fills_only_missing_actions():
    state = _make_state(
        ("don", Team.MAFIA),
        ("doctor", Team.CITIZENS),
        ("detective", Team.CITIZENS),
    )
    # Admin already played one action for the Don.
    admin_target = state.players[1].user_id
    state.current_actions[state.players[0].user_id] = NightAction(
        actor_id=state.players[0].user_id, role="don", action_type="kill", target_id=admin_target
    )

    await _submit_auto_actions(state, SandboxAutoPlayMode.AUTO.value)

    # Don's admin pick was preserved.
    assert state.current_actions[state.players[0].user_id].target_id == admin_target
    # Doctor + Detective got filled by auto.
    assert state.players[1].user_id in state.current_actions
    assert state.players[2].user_id in state.current_actions


@pytest.mark.asyncio
async def test_submit_voting_fills_only_missing_votes():
    state = _make_state(
        ("citizen", Team.CITIZENS),
        ("citizen", Team.CITIZENS),
        ("don", Team.MAFIA),
    )
    state.phase = Phase.VOTING
    # Admin voted for player[0] only.
    state.current_votes[state.players[0].user_id] = Vote(
        voter_id=state.players[0].user_id, target_id=state.players[2].user_id
    )
    await _submit_auto_actions(state, SandboxAutoPlayMode.AUTO.value)
    # Admin vote preserved.
    assert state.current_votes[state.players[0].user_id].target_id == state.players[2].user_id
    # Other two voters filled.
    assert state.players[1].user_id in state.current_votes
    assert state.players[2].user_id in state.current_votes


@pytest.mark.asyncio
async def test_submit_hanging_confirm_tallies_yes_no():
    state = _make_state(
        ("citizen", Team.CITIZENS),
        ("citizen", Team.CITIZENS),
        ("don", Team.MAFIA),
    )
    state.phase = Phase.HANGING_CONFIRM
    target_id = state.players[2].user_id
    state.current_round().extra["pending_hang_target"] = target_id

    await _submit_auto_actions(state, SandboxAutoPlayMode.RANDOM_ACTIONS.value)

    confirm = state.current_round().extra["hanging_confirm"]
    yes_total = state.current_round().extra["hang_yes_total"]
    no_total = state.current_round().extra["hang_no_total"]
    # Everyone voted exactly once.
    assert yes_total + no_total == 3
    # Tally keys are strings (Pydantic JSON serializability).
    assert all(isinstance(k, str) for k in confirm["yes"])
    assert all(isinstance(k, str) for k in confirm["no"])


@pytest.mark.asyncio
async def test_submit_does_nothing_when_no_pending_hang_target():
    state = _make_state(("citizen", Team.CITIZENS), ("don", Team.MAFIA))
    state.phase = Phase.HANGING_CONFIRM
    # No pending_hang_target in extra → must no-op.
    await _submit_auto_actions(state, SandboxAutoPlayMode.AUTO.value)
    assert "hang_yes_total" not in state.current_round().extra
    assert "hang_no_total" not in state.current_round().extra
