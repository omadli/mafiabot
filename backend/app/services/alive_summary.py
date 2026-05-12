"""Alive players summary — per-round numbered list + team/role breakdown.

Mirrors the @MafiaAzBot reference format observed at N=30.
"""

from __future__ import annotations

from collections import Counter

from app.core.state import GameState, Team

# Display order for roles within each team (for readability)
ROLE_DISPLAY = {
    "don": ("🤵🏻", "Don"),
    "mafia": ("🤵🏼", "Mafia"),
    "lawyer": ("👨‍💼", "Advokat"),
    "journalist": ("👩🏼‍💻", "Jurnalist"),
    "killer": ("🥷", "Ninza"),
    "citizen": ("👨🏼", "Tinch axoli"),
    "detective": ("🕵🏻‍♂", "Komissar katani"),
    "sergeant": ("👮🏻‍♂", "Serjant"),
    "doctor": ("👨🏻‍⚕", "Doktor"),
    "hooker": ("💃", "Kezuvchi"),
    "hobo": ("🧙‍♂", "Daydi"),
    "mayor": ("🎖", "Janob"),
    "lucky": ("🤞🏼", "Omadli"),
    "suicide": ("🤦🏼", "Suidsid"),
    "kamikaze": ("💣", "Afsungar"),
    "maniac": ("🔪", "Qotil"),
    "werewolf": ("🐺", "Bo'ri"),
    "mage": ("🧙", "Sehrgar"),
    "arsonist": ("🧟", "G'azabkor"),
    "crook": ("🤹", "Aferist"),
    "snitch": ("🤓", "Sotqin"),
}


def format_alive_summary(state: GameState) -> str:
    """Build numbered list + role breakdown by team.

    Format mirrors @MafiaAzBot:
        Tirik o'yinchilar:
        1. Username
        2. Username
        ...

        🤵🏼 Mafiya - 9
        🤵🏼 Mafia - 6, 👨‍💼 Advokat, 🤵🏻 Don

        🎯 Singleton - 7
        🐺 Bo'ri - 2, 🧟 G'azabkor, ...

        🤝 Tinch aholilar - 13
        ...

        Jami: 29
    """
    alive = sorted(state.alive_players(), key=lambda p: p.join_order)

    # Numbered list
    lines = ["<b>Tirik o'yinchilar:</b>"]
    for p in alive:
        name = _safe(p.first_name or (p.username or f"Player {p.user_id}"))
        lines.append(f"{p.join_order}. {name}")
    lines.append("")

    # Team breakdown — count roles per team
    team_buckets: dict[Team, list[str]] = {Team.MAFIA: [], Team.SINGLETON: [], Team.CITIZENS: []}
    for p in alive:
        team_buckets.setdefault(p.team, []).append(p.role)

    if team_buckets[Team.MAFIA]:
        lines.append(f"🤵🏼 <b>Mafiya</b> - {len(team_buckets[Team.MAFIA])}")
        lines.append(_format_role_counts(team_buckets[Team.MAFIA]))
        lines.append("")

    if team_buckets[Team.SINGLETON]:
        lines.append(f"🎯 <b>Singleton</b> - {len(team_buckets[Team.SINGLETON])}")
        lines.append(_format_role_counts(team_buckets[Team.SINGLETON]))
        lines.append("")

    if team_buckets[Team.CITIZENS]:
        lines.append(f"🤝 <b>Tinch aholilar</b> - {len(team_buckets[Team.CITIZENS])}")
        lines.append(_format_role_counts(team_buckets[Team.CITIZENS]))
        lines.append("")

    lines.append(f"<b>Jami:</b> {len(alive)}")
    return "\n".join(lines)


def _format_role_counts(roles: list[str]) -> str:
    """Format role counts as 'Role x N, Role, Role x N' (omit count if 1)."""
    counts = Counter(roles)
    parts = []
    for role, n in counts.most_common():
        emoji, name = ROLE_DISPLAY.get(role, ("❓", role))
        if n > 1:
            parts.append(f"{emoji} {name} - {n}")
        else:
            parts.append(f"{emoji} {name}")
    return ", ".join(parts)


def _safe(text: str) -> str:
    return text.replace("<", "&lt;").replace(">", "&gt;")
