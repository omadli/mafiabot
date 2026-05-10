"""Tests for win condition checks."""

from app.core.state import GameState, PlayerState, Team
from app.core.win_conditions import check_winner


def _make_state(*players: tuple[int, str, Team, bool]) -> GameState:
    """(user_id, role, team, alive) tuples → GameState."""
    return GameState(
        group_id=-1,
        chat_id=-1,
        players=[
            PlayerState(
                user_id=uid,
                first_name=f"P{uid}",
                join_order=idx + 1,
                role=role,
                team=team,
                alive=alive,
            )
            for idx, (uid, role, team, alive) in enumerate(players)
        ],
    )


def test_citizens_win_when_no_mafia():
    state = _make_state(
        (1, "detective", Team.CITIZENS, True),
        (2, "citizen", Team.CITIZENS, True),
        (3, "don", Team.MAFIA, False),
    )
    assert check_winner(state) == Team.CITIZENS


def test_mafia_wins_when_equal():
    state = _make_state(
        (1, "don", Team.MAFIA, True),
        (2, "citizen", Team.CITIZENS, True),
    )
    assert check_winner(state) == Team.MAFIA


def test_no_winner_mid_game():
    state = _make_state(
        (1, "don", Team.MAFIA, True),
        (2, "detective", Team.CITIZENS, True),
        (3, "citizen", Team.CITIZENS, True),
        (4, "doctor", Team.CITIZENS, True),
    )
    assert check_winner(state) is None
