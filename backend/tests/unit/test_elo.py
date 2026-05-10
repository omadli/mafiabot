"""Tests for ELO calculations."""

from app.services.elo_service import (
    calculate_team_elo_changes,
    expected_score,
    k_factor,
)


def test_k_factor_new_player():
    assert k_factor(games_played=10) == 40
    assert k_factor(games_played=29) == 40


def test_k_factor_default():
    assert k_factor(games_played=30) == 32
    assert k_factor(games_played=100) == 32


def test_k_factor_top():
    assert k_factor(games_played=100, is_top_50=True) == 16


def test_expected_score_equal_elo():
    assert expected_score(1000, 1000) == 0.5


def test_expected_score_higher_wins_more():
    higher = expected_score(1500, 1000)
    lower = expected_score(1000, 1500)
    assert higher > 0.9
    assert lower < 0.1
    assert abs((higher + lower) - 1.0) < 1e-6


def test_team_elo_winner_gains_loser_loses():
    winners = [(1, 1000, 50), (2, 1000, 50)]  # 2 winners
    losers = [(3, 1000, 50), (4, 1000, 50)]  # 2 losers
    changes = calculate_team_elo_changes(winners, losers)
    assert len(changes) == 4
    by_id = {c.user_id: c for c in changes}
    assert by_id[1].delta > 0
    assert by_id[2].delta > 0
    assert by_id[3].delta < 0
    assert by_id[4].delta < 0
    # Symmetry: winner gain = -loser loss (when ELOs equal)
    assert by_id[1].delta == -by_id[3].delta


def test_team_elo_underdog_gains_more():
    """Lower-ELO winner should gain more points."""
    underdog = [(1, 800, 100)]  # weak
    favorite = [(2, 1500, 100)]  # strong
    changes = calculate_team_elo_changes(underdog, favorite)
    by_id = {c.user_id: c for c in changes}
    # Underdog winning should get big boost
    assert by_id[1].delta >= 25  # most of K
