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


def test_mage_alone_alive_is_singleton_win_not_mafia():
    state = _make_state(
        (1, "mage", Team.SINGLETON, True),
        (2, "don", Team.MAFIA, False),
        (3, "citizen", Team.CITIZENS, False),
    )
    assert check_winner(state) == Team.SINGLETON


def test_crook_alone_alive_is_singleton_win():
    state = _make_state(
        (1, "crook", Team.SINGLETON, True),
        (2, "mafia", Team.MAFIA, False),
        (3, "doctor", Team.CITIZENS, False),
    )
    assert check_winner(state) == Team.SINGLETON


def test_werewolf_alone_alive_is_singleton_win():
    state = _make_state(
        (1, "werewolf", Team.SINGLETON, True),
        (2, "don", Team.MAFIA, False),
        (3, "detective", Team.CITIZENS, False),
    )
    assert check_winner(state) == Team.SINGLETON


def test_mafia_does_not_win_when_singletons_break_parity():
    # Bug reported by user: 3 mafia, 2 singletons, 3 citizens → was wrongly
    # giving Mafia the win on `3 >= 3` citizens parity. Mafia must outnumber
    # ALL non-mafia survivors (citizens + singletons).
    state = _make_state(
        (1, "don", Team.MAFIA, True),
        (2, "mafia", Team.MAFIA, True),
        (3, "lawyer", Team.MAFIA, True),
        (4, "mage", Team.SINGLETON, True),
        (5, "crook", Team.SINGLETON, True),
        (6, "detective", Team.CITIZENS, True),
        (7, "doctor", Team.CITIZENS, True),
        (8, "citizen", Team.CITIZENS, True),
    )
    assert check_winner(state) is None


def test_mafia_wins_parity_against_citizens_plus_singletons():
    # 3 mafia vs 2 citizens + 1 mage = 3 vs 3 → Mafia wins by parity.
    state = _make_state(
        (1, "don", Team.MAFIA, True),
        (2, "mafia", Team.MAFIA, True),
        (3, "lawyer", Team.MAFIA, True),
        (4, "mage", Team.SINGLETON, True),
        (5, "detective", Team.CITIZENS, True),
        (6, "doctor", Team.CITIZENS, True),
    )
    assert check_winner(state) == Team.MAFIA


def test_citizens_do_not_win_while_maniac_alive():
    # All Mafia dead but Maniac still hunting — game must continue so the
    # village has a chance to hang the Maniac.
    state = _make_state(
        (1, "detective", Team.CITIZENS, True),
        (2, "doctor", Team.CITIZENS, True),
        (3, "citizen", Team.CITIZENS, True),
        (4, "maniac", Team.SINGLETON, True),
        (5, "don", Team.MAFIA, False),
        (6, "mafia", Team.MAFIA, False),
    )
    assert check_winner(state) is None


def test_citizens_win_when_maniac_finally_hanged():
    # Same as above but after the village hangs the Maniac — citizens win.
    state = _make_state(
        (1, "detective", Team.CITIZENS, True),
        (2, "doctor", Team.CITIZENS, True),
        (3, "citizen", Team.CITIZENS, True),
        (4, "maniac", Team.SINGLETON, False),
        (5, "don", Team.MAFIA, False),
    )
    assert check_winner(state) == Team.CITIZENS


def test_citizens_win_with_passive_singleton_alive():
    # Mage is non-hostile — Citizens still win, Mage piggybacks via
    # winner_user_ids (orthogonal).
    state = _make_state(
        (1, "detective", Team.CITIZENS, True),
        (2, "citizen", Team.CITIZENS, True),
        (3, "mage", Team.SINGLETON, True),
        (4, "don", Team.MAFIA, False),
    )
    assert check_winner(state) == Team.CITIZENS


def test_mafia_wins_parity_when_only_maniac_left_on_other_side():
    # 1 mafia, 1 maniac, no citizens → mafia parity 1 >= 1 holds.
    state = _make_state(
        (1, "don", Team.MAFIA, True),
        (2, "maniac", Team.SINGLETON, True),
        (3, "citizen", Team.CITIZENS, False),
    )
    assert check_winner(state) == Team.MAFIA
