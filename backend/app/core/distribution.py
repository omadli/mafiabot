"""Role distribution: 4-30 players, 21 roles.

The default per-N role roster is an explicit lookup table built up
incrementally from N=4 by adding one role per N. This mirrors the user's
spec verbatim — each `_INCREMENTS` entry is the role added on top of
the previous N's roster.

Tweak the table here when the game designer changes the default
build-up; everything else (sandbox, group settings, tests) routes
through this single source of truth.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# Mafia-team roles. Used to pick a sensible substitute when an
# admin-disabled role appears in the default table — a mafia slot
# becomes plain `mafia`, anything else becomes `citizen`.
_MAFIA_TEAM_ROLES: frozenset[str] = frozenset({"don", "mafia", "lawyer", "journalist", "killer"})

# Hand-tuned roster for the smallest tables. From N=7 onwards each
# next-N roster is the previous one plus exactly one role
# (see `_INCREMENTS`), so we only need to spell out N=4..6 here.
_BASE_TABLE: dict[int, list[str]] = {
    4: ["citizen", "citizen", "detective", "don"],
    5: ["citizen", "citizen", "detective", "don", "doctor"],
    # N=6 swaps one citizen for `mafia` + adds `hooker`. The
    # build-up is not strictly additive at this step.
    6: ["citizen", "detective", "don", "mafia", "doctor", "hooker"],
}

# (N, role_added_on_top_of_previous_N). Edit this list to change the
# default build-up — the per-N table is derived from it at import time.
_INCREMENTS: list[tuple[int, str]] = [
    (7, "sergeant"),
    (8, "kamikaze"),
    (9, "mafia"),  # mafia=2
    (10, "werewolf"),
    (11, "hobo"),
    (12, "mafia"),  # mafia=3
    (13, "suicide"),
    (14, "maniac"),  # 🔪 Qotil (singleton)
    (15, "lawyer"),
    (16, "mafia"),  # mafia=4
    (17, "mayor"),
    (18, "kamikaze"),  # kamikaze=2
    (19, "mafia"),  # mafia=5
    (20, "mage"),
    (21, "arsonist"),
    (22, "werewolf"),  # werewolf=2
    (23, "journalist"),
    (24, "lucky"),
    (25, "mafia"),  # mafia=6
    (26, "snitch"),
    (27, "crook"),
    (28, "killer"),  # 🥷 Ninza (mafia)
    (29, "kamikaze"),  # kamikaze=3
    (30, "sergeant"),  # sergeant=2
]


def _build_distribution_table() -> dict[int, list[str]]:
    table: dict[int, list[str]] = {n: list(roles) for n, roles in _BASE_TABLE.items()}
    for n, role in _INCREMENTS:
        if n - 1 not in table:
            raise RuntimeError(f"Increment for N={n} but no roster for N={n - 1}")
        table[n] = table[n - 1] + [role]
        if len(table[n]) != n:
            raise RuntimeError(f"Distribution for N={n} has {len(table[n])} roles, expected {n}")
    return table


# N → list of role codes (length == N). Single source of truth for
# default role distribution; both `distribute_roles` and any UI that
# previews the roster (super-admin panel) should read from here.
DEFAULT_DISTRIBUTION: dict[int, list[str]] = _build_distribution_table()


@dataclass
class RoleAssignment:
    user_id: int
    role: str


def distribute_roles(
    user_ids: list[int],
    mafia_ratio: str = "low",  # retained for back-compat
    enabled_roles: dict[str, bool] | None = None,
    override: list[str] | None = None,
) -> list[RoleAssignment]:
    """Assign roles to N players from the default distribution table.

    `override` is an optional admin-provided role list for this N. When
    supplied and its length matches N exactly, the algorithm is bypassed
    entirely and these roles are dealt out (shuffled) verbatim. If the
    length doesn't match (stale config), we silently fall back to the
    default table.

    `enabled_roles` lets admins opt OUT of specific roles. A disabled
    role in the default roster is substituted with `mafia` for mafia
    slots and `citizen` for everything else. `don` is never disabled
    (the game needs at least one mafia leader); citizens and plain
    mafia aren't disable-able either.

    `mafia_ratio` is kept in the signature for back-compat with the
    previous algorithm but no longer affects the roster — the spec
    fixes mafia counts per N.
    """
    n = len(user_ids)
    if n < 4:
        raise ValueError(f"Min 4 players required, got {n}")
    if n > 30:
        raise ValueError(f"Max 30 players, got {n}")

    if override is not None and len(override) == n:
        roles = list(override)
    else:
        roles = list(DEFAULT_DISTRIBUTION[n])
        if enabled_roles:
            roles = _apply_enabled_filter(roles, enabled_roles)

    random.shuffle(roles)
    shuffled_users = list(user_ids)
    random.shuffle(shuffled_users)

    return [RoleAssignment(user_id=u, role=r) for u, r in zip(shuffled_users, roles, strict=False)]


def _apply_enabled_filter(roles: list[str], enabled: dict[str, bool]) -> list[str]:
    """Substitute admin-disabled roles with citizen/mafia by team.

    Don is always kept (the game requires a mafia leader). Plain
    `citizen` and `mafia` are also un-disable-able since they're the
    fallback slots themselves.
    """
    result: list[str] = []
    for role in roles:
        if role in ("don", "citizen", "mafia"):
            result.append(role)
            continue
        if enabled.get(role, True):
            result.append(role)
        elif role in _MAFIA_TEAM_ROLES:
            result.append("mafia")
        else:
            result.append("citizen")
    return result


# Backward-compat alias — used by game_service.distribute_mvp_roles().
distribute_mvp_roles = distribute_roles
