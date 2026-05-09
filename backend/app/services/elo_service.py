"""ELO rating algorithm — team-based.

K-factor:
    K=40 for new players (<30 games)
    K=16 for top players (top 50 by ELO globally)
    K=32 default

Expected score: 1 / (1 + 10^((opponent - me) / 400))
Actual: 1.0 if won, 0.0 if lost, 0.5 if draw
New ELO: round(elo + K * (actual - expected))
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class EloChange:
    user_id: int
    elo_before: int
    elo_after: int
    delta: int


def k_factor(games_played: int, is_top_50: bool = False) -> int:
    if is_top_50:
        return 16
    if games_played < 30:
        return 40
    return 32


def expected_score(my_elo: int, opp_avg_elo: int) -> float:
    return 1.0 / (1.0 + 10.0 ** ((opp_avg_elo - my_elo) / 400.0))


def calculate_team_elo_changes(
    winner_team_players: list[tuple[int, int, int]],  # [(user_id, elo, games_played), ...]
    loser_team_players: list[tuple[int, int, int]],
    top50_user_ids: set[int] | None = None,
) -> list[EloChange]:
    """Compute ELO deltas for both teams.

    Returns list with both winners and losers' changes.
    """
    top50_user_ids = top50_user_ids or set()

    if not winner_team_players or not loser_team_players:
        return []

    winners_avg = int(mean(p[1] for p in winner_team_players))
    losers_avg = int(mean(p[1] for p in loser_team_players))

    changes: list[EloChange] = []

    for user_id, elo, games in winner_team_players:
        k = k_factor(games, user_id in top50_user_ids)
        expected = expected_score(elo, losers_avg)
        delta = round(k * (1.0 - expected))
        changes.append(
            EloChange(user_id=user_id, elo_before=elo, elo_after=elo + delta, delta=delta)
        )

    for user_id, elo, games in loser_team_players:
        k = k_factor(games, user_id in top50_user_ids)
        expected = expected_score(elo, winners_avg)
        delta = round(k * (0.0 - expected))
        changes.append(
            EloChange(user_id=user_id, elo_before=elo, elo_after=elo + delta, delta=delta)
        )

    return changes
