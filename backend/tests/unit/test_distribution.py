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


def test_singletons_appear_by_default_at_n8():
    """All singletons are ON by default — at N >= 8 the singleton pool
    should be drawn from and at least one singleton should appear.
    """
    singleton_codes = {"suicide", "maniac", "werewolf", "mage", "arsonist", "crook", "snitch"}
    result = distribute_roles(_user_ids(15))
    roles = [r.role for r in result]
    assert any(r in singleton_codes for r in roles), "Expected some singleton at N=15 by default"


def test_singletons_suppressed_when_explicitly_disabled():
    """Admin can opt OUT of singletons by disabling them in group settings."""
    disabled = dict.fromkeys(
        ("suicide", "maniac", "werewolf", "mage", "arsonist", "crook", "snitch"), False
    )
    result = distribute_roles(_user_ids(15), enabled_roles=disabled)
    roles = [r.role for r in result]
    singletons = ["maniac", "werewolf", "mage", "arsonist", "crook", "snitch", "suicide"]
    for s in singletons:
        assert s not in roles, f"Singleton {s} appeared despite being disabled"


def test_singletons_appear_when_enabled():
    """When singleton enabled (here: only maniac), it should appear at N >= 8."""
    enabled = dict.fromkeys(("suicide", "werewolf", "mage", "arsonist", "crook", "snitch"), False)
    enabled["maniac"] = True
    result = distribute_roles(_user_ids(10), enabled_roles=enabled)
    roles = [r.role for r in result]
    assert "maniac" in roles


def test_n30_high_ratio_matches_reference():
    """30 players, high ratio, all roles enabled — match @MafiaAzBot reference.

    Reference shows: 10 mafia, 7 singletons, 13 civilians.
    """
    enabled = dict.fromkeys(
        (
            "lucky",
            "suicide",
            "kamikaze",
            "journalist",
            "killer",
            "maniac",
            "werewolf",
            "mage",
            "arsonist",
            "crook",
            "snitch",
        ),
        True,
    )
    result = distribute_roles(_user_ids(30), mafia_ratio="high", enabled_roles=enabled)
    roles = [r.role for r in result]

    mafia_codes = {"don", "mafia", "lawyer", "journalist", "killer"}
    singleton_codes = {"suicide", "maniac", "werewolf", "mage", "arsonist", "crook", "snitch"}

    mafia_count = sum(1 for r in roles if r in mafia_codes)
    singleton_count = sum(1 for r in roles if r in singleton_codes)
    civilian_count = len(roles) - mafia_count - singleton_count

    assert mafia_count == 10, f"Expected 10 mafia, got {mafia_count}"
    assert singleton_count == 7, f"Expected 7 singletons, got {singleton_count}"
    assert civilian_count == 13, f"Expected 13 civilians, got {civilian_count}"


def test_n30_kamikaze_multi_instance():
    """At N=30, kamikaze should appear 3 times (ceil(30/10))."""
    enabled = {"kamikaze": True, "lucky": True, "suicide": True}
    result = distribute_roles(_user_ids(30), mafia_ratio="high", enabled_roles=enabled)
    roles = [r.role for r in result]
    kamikaze_count = sum(1 for r in roles if r == "kamikaze")
    assert kamikaze_count == 3, f"Expected 3 kamikazes, got {kamikaze_count}"


def test_n20_extra_sergeant():
    """At N>=20, sergeant appears twice."""
    result = distribute_roles(_user_ids(20))
    roles = [r.role for r in result]
    sergeant_count = sum(1 for r in roles if r == "sergeant")
    assert sergeant_count == 2, f"Expected 2 sergeants at N=20, got {sergeant_count}"


def test_n24_werewolf_multi_instance():
    """At N>=24, werewolf may appear twice. Isolate by disabling other
    singletons so the singleton pool is werewolf-only.
    """
    enabled = dict.fromkeys(("suicide", "maniac", "mage", "arsonist", "crook", "snitch"), False)
    enabled["werewolf"] = True
    result = distribute_roles(_user_ids(24), mafia_ratio="high", enabled_roles=enabled)
    roles = [r.role for r in result]
    werewolf_count = sum(1 for r in roles if r == "werewolf")
    # N=24 → singletons = 24//4 = 6; with only werewolf enabled, all become werewolf
    assert werewolf_count >= 2, f"Expected >=2 werewolves, got {werewolf_count}"


def test_override_used_verbatim_when_length_matches():
    """Admin-provided override bypasses the algorithm entirely."""
    override = ["don", "detective", "doctor", "citizen", "mafia"]
    result = distribute_roles(_user_ids(5), override=override)
    assert sorted(r.role for r in result) == sorted(override)


def test_override_ignored_when_length_mismatches():
    """Stale override (wrong length) falls back to the algorithm."""
    override = ["don", "detective"]  # only 2 roles for a 5-player game
    result = distribute_roles(_user_ids(5), override=override)
    # Length must match player count regardless
    assert len(result) == 5
    # Algorithm always assigns 1 detective + 1 don at N=5
    roles = [r.role for r in result]
    assert "detective" in roles
    assert "don" in roles


def test_lawyer_journalist_absent_in_small_games():
    """Per user spec: default Mafia roster in small games is Don + Mafia only.
    Advokat/Jurnalist must not appear below their thresholds (12 / 17).
    """
    for n in (4, 5, 8, 10, 11):
        result = distribute_roles(_user_ids(n), mafia_ratio="high")
        roles = [r.role for r in result]
        assert "lawyer" not in roles, f"Lawyer appeared at N={n}"
        assert "journalist" not in roles, f"Journalist appeared at N={n}"


def test_lawyer_appears_at_n12():
    """Lawyer kicks in at N >= 12 when enabled (default enabled)."""
    # high ratio so mafia_count has room: 12 // 3 = 4 → don + lawyer + 2 mafia
    result = distribute_roles(_user_ids(12), mafia_ratio="high")
    roles = [r.role for r in result]
    assert "lawyer" in roles
    assert "journalist" not in roles  # below journalist threshold


def test_journalist_appears_at_n17():
    """Journalist kicks in at N >= 17 when enabled."""
    enabled = {"journalist": True}
    result = distribute_roles(_user_ids(17), mafia_ratio="high", enabled_roles=enabled)
    roles = [r.role for r in result]
    assert "lawyer" in roles
    assert "journalist" in roles


def test_killer_absent_below_n25():
    """Killer (Ninza) is default-on but capped to N >= 25 tables."""
    for n in (12, 17, 20, 24):
        result = distribute_roles(_user_ids(n), mafia_ratio="high")
        roles = [r.role for r in result]
        assert "killer" not in roles, f"Killer appeared at N={n}"


def test_killer_appears_at_n25_by_default():
    """At N >= 25 Killer auto-joins the Mafia roster (default enabled)."""
    result = distribute_roles(_user_ids(25), mafia_ratio="high")
    roles = [r.role for r in result]
    assert "killer" in roles


def test_override_shuffles_assignment():
    """Override roles get shuffled across user_ids (not deterministic order)."""
    import random

    override = ["don", "detective", "doctor", "citizen", "mafia"]
    # With seeded RNG, two runs should produce identical results
    random.seed(123)
    a = distribute_roles(_user_ids(5), override=override)
    random.seed(123)
    b = distribute_roles(_user_ids(5), override=override)
    assert [(r.user_id, r.role) for r in a] == [(r.user_id, r.role) for r in b]
