"""Role distribution: 4-30 players, 21 roles, mafia_ratio aware.

Algorithm:
1. Calculate mafia count = floor(N * ratio) where ratio in {1/4, 1/3}.
2. Mafia composition (priority order):
   - 1 Don (always)
   - +1 Lawyer (if N >= 6 and lawyer enabled)
   - +1 Journalist (if N >= 8 and journalist enabled)
   - +1 Killer/Ninza (if N >= 10 and killer enabled)
   - rest filled with plain Mafia
3. Singleton count = min(2, N // 8) — N>=8: 1, N>=16: 2.
   Picked randomly from enabled singleton roles.
4. Civilians = remainder. Composition (priority order):
   - 1 Detective (always)
   - +1 Doctor (if N >= 5 and doctor enabled)
   - +1 Hooker (if N >= 6 and hooker enabled)
   - +1 Sergeant (if N >= 8 and sergeant enabled)
   - +1 Mayor (if N >= 10 and mayor enabled)
   - +1 Hobo (if N >= 12 and hobo enabled)
   - +1 Lucky (if N >= 14 and lucky enabled)
   - rest filled with plain Citizens
5. Shuffle and assign to user_ids.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

SINGLETON_ROLES = ["maniac", "werewolf", "mage", "arsonist", "crook", "snitch"]

# Civilian roles in priority order (excluding citizen which is filler)
CIVILIAN_PRIORITY: list[tuple[str, int]] = [
    ("detective", 4),
    ("doctor", 5),
    ("hooker", 6),
    ("sergeant", 8),
    ("mayor", 10),
    ("hobo", 12),
    ("lucky", 14),
    # special: suicide, kamikaze — opt-in via enabled_roles only
]

# Mafia roles in priority (excluding plain mafia which is filler)
MAFIA_PRIORITY: list[tuple[str, int]] = [
    ("lawyer", 6),
    ("journalist", 8),
    ("killer", 10),
]


@dataclass
class RoleAssignment:
    user_id: int
    role: str


def distribute_roles(
    user_ids: list[int],
    mafia_ratio: str = "low",
    enabled_roles: dict[str, bool] | None = None,
) -> list[RoleAssignment]:
    """Assign roles to N players based on settings.

    Args:
        user_ids: list of player user_ids (4..30)
        mafia_ratio: 'low' (1/4) or 'high' (1/3)
        enabled_roles: {"detective": True, ...} — which optional roles are available

    Returns:
        list of RoleAssignment (shuffled).
    """
    n = len(user_ids)
    if n < 4:
        raise ValueError(f"Min 4 players required, got {n}")
    if n > 30:
        raise ValueError(f"Max 30 players, got {n}")

    enabled = _default_enabled()
    if enabled_roles:
        enabled.update(enabled_roles)

    # 1. Mafia count
    mafia_count = max(1, n // 3) if mafia_ratio == "high" else max(1, n // 4)

    # 2. Mafia composition
    mafia_roles: list[str] = ["don"]
    for role_code, threshold in MAFIA_PRIORITY:
        if len(mafia_roles) >= mafia_count:
            break
        if n >= threshold and enabled.get(role_code, False):
            mafia_roles.append(role_code)
    while len(mafia_roles) < mafia_count:
        mafia_roles.append("mafia")

    # 3. Singletons
    target_singletons = min(2, n // 8)
    available_singletons = [r for r in SINGLETON_ROLES if enabled.get(r, False)]
    if target_singletons > len(available_singletons):
        target_singletons = len(available_singletons)
    chosen_singletons = (
        random.sample(available_singletons, target_singletons) if target_singletons > 0 else []
    )

    # 4. Civilians
    civilian_count = n - len(mafia_roles) - len(chosen_singletons)
    civilian_roles: list[str] = []
    if enabled.get("detective", True):
        civilian_roles.append("detective")
    for role_code, threshold in CIVILIAN_PRIORITY[1:]:  # skip detective (already added)
        if len(civilian_roles) >= civilian_count:
            break
        if n >= threshold and enabled.get(role_code, False):
            civilian_roles.append(role_code)

    # Special opt-in roles (suicide, kamikaze) — require explicit enabled
    for special in ("suicide", "kamikaze"):
        if len(civilian_roles) >= civilian_count:
            break
        if enabled.get(special, False) and n >= 7:
            civilian_roles.append(special)

    # Fill rest with plain citizens
    while len(civilian_roles) < civilian_count:
        civilian_roles.append("citizen")
    if len(civilian_roles) > civilian_count:
        civilian_roles = civilian_roles[:civilian_count]

    # 5. Combine + shuffle
    all_roles = mafia_roles + chosen_singletons + civilian_roles
    if len(all_roles) != n:
        raise RuntimeError(
            f"Distribution mismatch: {len(all_roles)} roles for {n} players "
            f"(mafia={len(mafia_roles)}, singleton={len(chosen_singletons)}, "
            f"civilian={len(civilian_roles)})"
        )

    random.shuffle(all_roles)
    shuffled_users = user_ids.copy()
    random.shuffle(shuffled_users)

    return [
        RoleAssignment(user_id=u, role=r) for u, r in zip(shuffled_users, all_roles, strict=False)
    ]


def _default_enabled() -> dict[str, bool]:
    """Default: civilian core roles enabled, others off (admin opt-in)."""
    return {
        # Civilians
        "citizen": True,
        "detective": True,
        "doctor": True,
        "hooker": True,
        "sergeant": True,
        "mayor": True,
        "hobo": True,
        "lucky": False,
        "suicide": False,
        "kamikaze": False,
        # Mafia
        "don": True,
        "mafia": True,
        "lawyer": True,
        "journalist": False,
        "killer": False,
        # Singletons
        "maniac": False,
        "werewolf": False,
        "mage": False,
        "arsonist": False,
        "crook": False,
        "snitch": False,
    }


# Backward-compat alias
distribute_mvp_roles = distribute_roles
