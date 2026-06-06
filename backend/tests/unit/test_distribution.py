"""Tests for role distribution table.

The default per-N roster is a hand-curated lookup table in
`app/core/distribution.py:DEFAULT_DISTRIBUTION`. These tests pin the
roster shape for each N so accidental edits to the build-up are caught.
"""

from __future__ import annotations

import pytest
from app.core.distribution import DEFAULT_DISTRIBUTION, distribute_roles

_MAFIA_TEAM = {"don", "mafia", "lawyer", "journalist", "killer"}
_SINGLETONS = {"suicide", "maniac", "werewolf", "mage", "arsonist", "crook", "snitch"}


def _user_ids(n: int) -> list[int]:
    return list(range(100, 100 + n))


def _count(roles: list[str], code: str) -> int:
    return sum(1 for r in roles if r == code)


# === Basic validation ===


def test_min_4_players_works():
    result = distribute_roles(_user_ids(4))
    assert len(result) == 4
    roles = [r.role for r in result]
    assert "don" in roles
    assert "detective" in roles
    assert _count(roles, "citizen") == 2


def test_below_min_raises():
    with pytest.raises(ValueError, match="Min 4"):
        distribute_roles(_user_ids(3))


def test_above_max_raises():
    with pytest.raises(ValueError, match="Max 30"):
        distribute_roles(_user_ids(31))


def test_table_covers_4_through_30():
    for n in range(4, 31):
        assert n in DEFAULT_DISTRIBUTION, f"Missing distribution for N={n}"
        assert len(DEFAULT_DISTRIBUTION[n]) == n, (
            f"N={n} roster has {len(DEFAULT_DISTRIBUTION[n])} roles"
        )


def test_role_count_matches_n_for_every_size():
    for n in range(4, 31):
        result = distribute_roles(_user_ids(n))
        assert len(result) == n, f"Failed for N={n}"


def test_unique_user_ids_preserved():
    user_ids = _user_ids(8)
    result = distribute_roles(user_ids)
    assert {r.user_id for r in result} == set(user_ids)


# === Pin the exact spec, low-N ===


def test_n4_roster():
    assert sorted(DEFAULT_DISTRIBUTION[4]) == ["citizen", "citizen", "detective", "don"]


def test_n5_adds_doctor():
    roles = DEFAULT_DISTRIBUTION[5]
    assert _count(roles, "citizen") == 2
    assert "doctor" in roles
    assert "detective" in roles
    assert "don" in roles


def test_n6_introduces_mafia_and_hooker_at_cost_of_a_citizen():
    roles = DEFAULT_DISTRIBUTION[6]
    assert _count(roles, "citizen") == 1
    assert _count(roles, "mafia") == 1
    assert "hooker" in roles
    assert "doctor" in roles


def test_n7_adds_sergeant_not_hobo():
    """Per spec swap: Sergeant lands at N=7, Hobo waits till N=11."""
    roles = DEFAULT_DISTRIBUTION[7]
    assert "sergeant" in roles
    assert "hobo" not in roles


def test_n8_adds_first_kamikaze():
    assert "kamikaze" in DEFAULT_DISTRIBUTION[8]
    # Only one singleton at N=8 — keeps the small game civilian-heavy.
    assert _count(DEFAULT_DISTRIBUTION[8], "kamikaze") == 1


def test_n9_grows_mafia_to_2():
    assert _count(DEFAULT_DISTRIBUTION[9], "mafia") == 2


def test_n10_adds_werewolf():
    assert "werewolf" in DEFAULT_DISTRIBUTION[10]


def test_n11_adds_hobo():
    """Sergeant/Hobo swap: Hobo joins at N=11 (not N=7)."""
    assert "hobo" in DEFAULT_DISTRIBUTION[11]


# === Mid-range pins ===


def test_n14_adds_maniac_qotil_singleton():
    """At N=14 we get the singleton 🔪 Qotil (`maniac`), NOT the mafia
    🥷 Ninza (`killer`) — Killer doesn't show up until N=28.
    """
    assert "maniac" in DEFAULT_DISTRIBUTION[14]
    assert "killer" not in DEFAULT_DISTRIBUTION[14]


def test_n15_adds_lawyer():
    assert "lawyer" in DEFAULT_DISTRIBUTION[15]


def test_n17_adds_mayor_not_lucky():
    """Mayor/Lucky swap: Mayor lands at N=17, Lucky at N=24."""
    assert "mayor" in DEFAULT_DISTRIBUTION[17]
    assert "lucky" not in DEFAULT_DISTRIBUTION[17]


def test_n18_grows_kamikaze_to_2():
    assert _count(DEFAULT_DISTRIBUTION[18], "kamikaze") == 2


def test_n22_grows_werewolf_to_2():
    assert _count(DEFAULT_DISTRIBUTION[22], "werewolf") == 2


def test_n23_adds_journalist():
    assert "journalist" in DEFAULT_DISTRIBUTION[23]


def test_n24_adds_lucky_not_mayor():
    """Per swap: Lucky arrives at N=24 (Mayor was already in by then)."""
    assert "lucky" in DEFAULT_DISTRIBUTION[24]


# === High-N pins ===


def test_n28_adds_killer_ninza():
    """N=28 increment is the mafia 🥷 Ninza (`killer`), not a 2nd Qotil."""
    assert "killer" in DEFAULT_DISTRIBUTION[28]
    assert _count(DEFAULT_DISTRIBUTION[28], "killer") == 1
    # And maniac count must STAY at 1 here (no 2nd Qotil per the swap).
    assert _count(DEFAULT_DISTRIBUTION[28], "maniac") == 1


def test_n29_grows_kamikaze_to_3():
    assert _count(DEFAULT_DISTRIBUTION[29], "kamikaze") == 3


def test_n30_grows_sergeant_to_2():
    assert _count(DEFAULT_DISTRIBUTION[30], "sergeant") == 2


def test_n30_final_role_breakdown():
    """Sanity: the N=30 roster matches the user's spec total."""
    roles = DEFAULT_DISTRIBUTION[30]
    mafia = sum(1 for r in roles if r in _MAFIA_TEAM)
    singleton = sum(1 for r in roles if r in _SINGLETONS)
    civilian = len(roles) - mafia - singleton
    # Spec at N=30: 1 don + 6 mafia + 1 lawyer + 1 journalist + 1 killer = 10
    # singletons: 1 suicide + 1 maniac + 2 werewolf + 1 mage + 1 arsonist + 1 snitch + 1 crook = 8
    # civilians: 1 citizen + 1 detective + 1 doctor + 1 hooker + 2 sergeant + 1 hobo + 1 mayor + 1 lucky + 3 kamikaze = 12
    assert mafia == 10
    assert singleton == 8
    assert civilian == 12


def test_no_killer_below_n28():
    """🥷 Ninza is exclusive to N=28+ in the default table."""
    for n in range(4, 28):
        assert "killer" not in DEFAULT_DISTRIBUTION[n], f"Killer leaked into N={n}"


def test_no_journalist_below_n23():
    for n in range(4, 23):
        assert "journalist" not in DEFAULT_DISTRIBUTION[n]


def test_no_lawyer_below_n15():
    for n in range(4, 15):
        assert "lawyer" not in DEFAULT_DISTRIBUTION[n]


# === enabled_roles substitution ===


def test_disabling_a_singleton_substitutes_citizen():
    """Disabled singleton becomes a citizen in the same slot — never silently
    dropped (otherwise N players would receive N-1 roles)."""
    result = distribute_roles(_user_ids(8), enabled_roles={"kamikaze": False})
    roles = [r.role for r in result]
    assert "kamikaze" not in roles
    # N=8 had 1 kamikaze → now an extra citizen.
    assert _count(roles, "citizen") == _count(DEFAULT_DISTRIBUTION[8], "citizen") + 1


def test_disabling_a_mafia_role_substitutes_plain_mafia():
    """Disabling Lawyer at N=15 keeps the mafia headcount intact via `mafia`."""
    result = distribute_roles(_user_ids(15), enabled_roles={"lawyer": False})
    roles = [r.role for r in result]
    assert "lawyer" not in roles
    spec_mafia = sum(1 for r in DEFAULT_DISTRIBUTION[15] if r in _MAFIA_TEAM)
    actual_mafia = sum(1 for r in roles if r in _MAFIA_TEAM)
    assert actual_mafia == spec_mafia


def test_don_cannot_be_disabled_via_enabled_roles():
    """Disabling Don in admin settings is meaningless — every game needs one."""
    result = distribute_roles(_user_ids(8), enabled_roles={"don": False})
    roles = [r.role for r in result]
    assert "don" in roles


# === Override path (admin-supplied verbatim list) ===


def test_override_used_verbatim_when_length_matches():
    override = ["don", "detective", "doctor", "citizen", "mafia"]
    result = distribute_roles(_user_ids(5), override=override)
    assert sorted(r.role for r in result) == sorted(override)


def test_override_ignored_when_length_mismatches():
    """Stale override (wrong length) falls back to the default table."""
    override = ["don", "detective"]  # 2 roles for a 5-player game
    result = distribute_roles(_user_ids(5), override=override)
    assert len(result) == 5
    roles = [r.role for r in result]
    assert "don" in roles
    assert "detective" in roles


def test_override_shuffles_assignment_deterministically():
    """Same RNG seed → same shuffle (sanity check for the override path)."""
    import random

    override = ["don", "detective", "doctor", "citizen", "mafia"]
    random.seed(123)
    a = distribute_roles(_user_ids(5), override=override)
    random.seed(123)
    b = distribute_roles(_user_ids(5), override=override)
    assert [(r.user_id, r.role) for r in a] == [(r.user_id, r.role) for r in b]


# === mafia_ratio is now a no-op back-compat parameter ===


def test_mafia_ratio_parameter_is_accepted_but_ignored():
    """`mafia_ratio` lingers in the signature so existing callers compile,
    but it no longer alters the roster — the table is fixed per N."""
    low = distribute_roles(_user_ids(10), mafia_ratio="low")
    high = distribute_roles(_user_ids(10), mafia_ratio="high")
    low_mafia = sum(1 for r in low if r.role in _MAFIA_TEAM)
    high_mafia = sum(1 for r in high if r.role in _MAFIA_TEAM)
    assert low_mafia == high_mafia
