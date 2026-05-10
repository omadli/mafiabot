"""Tests for role distribution algorithm."""

import pytest
from app.core.distribution import distribute_roles


def _user_ids(n: int) -> list[int]:
    return list(range(100, 100 + n))


def test_min_4_players_works():
    result = distribute_roles(_user_ids(4))
    assert len(result) == 4
    roles = [r.role for r in result]
    assert "don" in roles  # always at least 1 mafia
    assert "detective" in roles  # always detective


def test_below_min_raises():
    with pytest.raises(ValueError, match="Min 4"):
        distribute_roles(_user_ids(3))


def test_above_max_raises():
    with pytest.raises(ValueError, match="Max 30"):
        distribute_roles(_user_ids(31))


def test_low_ratio_n10():
    result = distribute_roles(_user_ids(10), mafia_ratio="low")
    roles = [r.role for r in result]
    # low: mafia = N // 4 = 2 (don + 1)
    mafia_count = sum(1 for r in roles if r in ("don", "mafia", "lawyer", "journalist", "killer"))
    assert mafia_count == 2


def test_high_ratio_n9_more_mafia():
    result = distribute_roles(_user_ids(9), mafia_ratio="high")
    roles = [r.role for r in result]
    mafia_count = sum(1 for r in roles if r in ("don", "mafia", "lawyer", "journalist", "killer"))
    # high: mafia = N // 3 = 3
    assert mafia_count == 3


def test_unique_user_ids_preserved():
    user_ids = _user_ids(8)
    result = distribute_roles(user_ids)
    assigned_ids = {r.user_id for r in result}
    assert assigned_ids == set(user_ids)


def test_role_count_matches_n():
    for n in (4, 5, 7, 10, 15, 20, 30):
        result = distribute_roles(_user_ids(n))
        assert len(result) == n, f"Failed for N={n}"


def test_singletons_only_when_enabled():
    """Singletons disabled by default — should not appear in distribution."""
    result = distribute_roles(_user_ids(15))
    roles = [r.role for r in result]
    singletons = ["maniac", "werewolf", "mage", "arsonist", "crook", "snitch"]
    for s in singletons:
        assert s not in roles, f"Singleton {s} appeared without being enabled"


def test_singletons_appear_when_enabled():
    """When singleton enabled, it should appear at N >= 8."""
    enabled = {"maniac": True}
    result = distribute_roles(_user_ids(10), enabled_roles=enabled)
    roles = [r.role for r in result]
    assert "maniac" in roles
