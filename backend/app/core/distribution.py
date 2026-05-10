"""Role distribution: 4-30 players, 21 roles, mafia_ratio aware.

Algorithm (matches @MafiaAzBot reference at N=30):
1. Mafia count = floor(N * ratio) where ratio in {1/4, 1/3}.
2. Mafia composition (priority order):
   - 1 Don (always)
   - +1 Lawyer (if N >= 6 and lawyer enabled)
   - +1 Journalist (if N >= 8 and journalist enabled)
   - +1 Killer/Ninza (if N >= 10 and killer enabled)
   - rest filled with plain Mafia
3. Singleton count = max(1, N // 4) at N >= 8 (else 0).
   - Multi-instance: Werewolf x2 at N >= 24, Maniac x2 at N >= 28.
4. Civilians = remainder. Composition (priority order):
   - 1 Detective (always)
   - +1 Doctor (if N >= 5 and doctor enabled)
   - +1 Hooker (if N >= 6 and hooker enabled)
   - +1 Sergeant (if N >= 8 and sergeant enabled)
   - +1 extra Sergeant (if N >= 20)
   - +1 Mayor (if N >= 10 and mayor enabled)
   - +1 Hobo (if N >= 12 and hobo enabled)
   - +1 Lucky (if N >= 14 and lucky enabled)
   - +1 Suicide (if N >= 16 and suicide enabled)
   - +Kamikaze x ceil(N/10) (if N >= 18 and kamikaze enabled)
   - rest filled with plain Citizens
5. Shuffle and assign to user_ids.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# Singletons that may appear multiple times in a single game at high N.
SINGLETON_MULTI_THRESHOLDS: dict[str, int] = {
    "werewolf": 24,  # +1 extra werewolf at N>=24
    "maniac": 28,  # +1 extra maniac at N>=28
}

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
    ("suicide", 16),
    # kamikaze handled separately (multi-instance)
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
    """Assign roles to N players based on settings."""
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

    # 3. Singletons — scale with N
    target_singletons = max(1, n // 4) if n >= 8 else 0

    available_singletons = [r for r in SINGLETON_ROLES if enabled.get(r, False)]
    chosen_singletons: list[str] = []
    if available_singletons and target_singletons > 0:
        # Pick unique ones first
        unique_pick = random.sample(
            available_singletons, min(target_singletons, len(available_singletons))
        )
        chosen_singletons.extend(unique_pick)

        # Multi-instance for high N: add extra werewolf/maniac if conditions met
        for role, threshold in SINGLETON_MULTI_THRESHOLDS.items():
            if (
                n >= threshold
                and role in unique_pick
                and len(chosen_singletons) < target_singletons
            ):
                chosen_singletons.append(role)

        # If still not enough, allow duplicates from chosen pool
        while len(chosen_singletons) < target_singletons and unique_pick:
            chosen_singletons.append(random.choice(unique_pick))

    # 4. Civilians
    civilian_count = n - len(mafia_roles) - len(chosen_singletons)
    if civilian_count < 0:
        # Singleton overflow — trim
        chosen_singletons = chosen_singletons[: n - len(mafia_roles)]
        civilian_count = 0

    civilian_roles: list[str] = []
    if enabled.get("detective", True) and civilian_count > 0:
        civilian_roles.append("detective")
    for role_code, threshold in CIVILIAN_PRIORITY[1:]:
        if len(civilian_roles) >= civilian_count:
            break
        if n >= threshold and enabled.get(role_code, False):
            civilian_roles.append(role_code)

    # Extra sergeant at N>=20
    if (
        n >= 20
        and enabled.get("sergeant", True)
        and civilian_roles.count("sergeant") < 2
        and len(civilian_roles) < civilian_count
    ):
        civilian_roles.append("sergeant")

    # Multi-instance kamikaze: ceil(N/10) at N>=18
    if n >= 18 and enabled.get("kamikaze", False):
        kamikaze_count = (n + 9) // 10  # ceil(N/10)
        for _ in range(kamikaze_count):
            if len(civilian_roles) >= civilian_count:
                break
            civilian_roles.append("kamikaze")

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
        "don": True,
        "mafia": True,
        "lawyer": True,
        "journalist": False,
        "killer": False,
        "maniac": False,
        "werewolf": False,
        "mage": False,
        "arsonist": False,
        "crook": False,
        "snitch": False,
    }


# Backward-compat alias
distribute_mvp_roles = distribute_roles
