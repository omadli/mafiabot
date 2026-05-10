"""Tests for GameState (Redis JSON serialization)."""

from app.core.state import (
    GameState,
    Phase,
    PlayerState,
    Team,
)


def test_state_round_trip_redis():
    state = GameState(
        group_id=-1001234567,
        chat_id=-1001234567,
        phase=Phase.NIGHT,
        round_num=2,
        players=[
            PlayerState(user_id=100, first_name="Ali", join_order=1, role="don", team=Team.MAFIA),
            PlayerState(
                user_id=101,
                first_name="Vali",
                join_order=2,
                role="detective",
                team=Team.CITIZENS,
            ),
        ],
    )
    serialized = state.to_redis()
    restored = GameState.from_redis(serialized)
    assert restored.group_id == state.group_id
    assert len(restored.players) == 2
    assert restored.players[0].role == "don"
    assert restored.phase == Phase.NIGHT


def test_alive_helpers():
    state = GameState(
        group_id=-1001,
        chat_id=-1001,
        players=[
            PlayerState(
                user_id=1, first_name="A", join_order=1, role="citizen", team=Team.CITIZENS
            ),
            PlayerState(
                user_id=2,
                first_name="B",
                join_order=2,
                role="don",
                team=Team.MAFIA,
                alive=False,
            ),
            PlayerState(
                user_id=3,
                first_name="C",
                join_order=3,
                role="detective",
                team=Team.CITIZENS,
            ),
        ],
    )
    assert len(state.alive_players()) == 2
    assert len(state.alive_by_team(Team.CITIZENS)) == 2
    assert len(state.alive_by_team(Team.MAFIA)) == 0
    assert state.get_player(2) is not None
    assert state.get_player(999) is None


def test_current_round_creates_log_per_round():
    state = GameState(group_id=-1, chat_id=-1, round_num=1)
    log1 = state.current_round()
    log2 = state.current_round()
    assert log1 is log2  # same round → same log

    state.round_num = 2
    log3 = state.current_round()
    assert log3 is not log1
    assert len(state.rounds) == 2


def test_history_dict_serializable():
    state = GameState(
        group_id=-1,
        chat_id=-1,
        winner_team=Team.CITIZENS,
        players=[
            PlayerState(
                user_id=1,
                first_name="X",
                join_order=1,
                role="citizen",
                team=Team.CITIZENS,
            ),
        ],
    )
    history = state.to_history_dict()
    assert "players" in history
    assert "rounds" in history
    assert history["winner_team"] == Team.CITIZENS
