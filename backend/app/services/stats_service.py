"""Statistics service — populate GameResult, UserStats, GroupUserStats on game finish."""

from __future__ import annotations

import time
from datetime import UTC

from loguru import logger
from tortoise.transactions import in_transaction

from app.core.state import DeathReason, GameState, Phase, Team
from app.db.models import (
    Game,
    GameResult,
    GroupStats,
    GroupUserStats,
    User,
    UserStats,
)
from app.services.elo_service import EloChange, calculate_team_elo_changes

XP_WIN = 50
XP_LOSS = 10
XP_SURVIVED_BONUS = 20
DOLLARS_WIN = 10
DOLLARS_LOSS = 2


async def finalize_game_stats(state: GameState) -> None:
    """Called after Game.history is saved. Persists GameResult + updates UserStats/GroupUserStats."""
    if state.winner_team is None:
        logger.info(f"Game {state.id} has no winner, skipping stats")
        return

    game = await Game.get_or_none(id=state.id)
    if game is None:
        logger.warning(f"Game {state.id} not found in DB for stats")
        return

    # Compute ELO changes — global
    winners_global = []
    losers_global = []
    for player in state.players:
        user = await User.get_or_none(id=player.user_id)
        if user is None:
            continue
        stats = await UserStats.get_or_create(user=user)
        stats_obj = stats[0] if isinstance(stats, tuple) else stats
        won = player.user_id in state.winner_user_ids
        bucket = winners_global if won else losers_global
        bucket.append((player.user_id, stats_obj.elo, stats_obj.games_total))

    global_elo_changes = calculate_team_elo_changes(winners_global, losers_global)
    elo_change_map = {c.user_id: c for c in global_elo_changes}

    # Compute ELO changes — per group
    group_winners: list[tuple[int, int, int]] = []
    group_losers: list[tuple[int, int, int]] = []
    for player in state.players:
        gus, _ = await GroupUserStats.get_or_create(user_id=player.user_id, group_id=state.group_id)
        won = player.user_id in state.winner_user_ids
        bucket = group_winners if won else group_losers
        bucket.append((player.user_id, gus.elo, gus.games_total))

    group_elo_changes = calculate_team_elo_changes(group_winners, group_losers)
    group_elo_map = {c.user_id: c for c in group_elo_changes}

    duration = (state.finished_at or int(time.time())) - (state.started_at or 0)

    async with in_transaction():
        for player in state.players:
            won = player.user_id in state.winner_user_ids
            global_change = elo_change_map.get(player.user_id)
            group_change = group_elo_map.get(player.user_id)
            if global_change is None or group_change is None:
                continue

            xp_earned = (XP_WIN if won else XP_LOSS) + (XP_SURVIVED_BONUS if player.alive else 0)
            dollars_earned = DOLLARS_WIN if won else DOLLARS_LOSS

            # 1. GameResult INSERT
            await GameResult.create(
                user_id=player.user_id,
                game_id=state.id,
                group_id=state.group_id,
                role=player.role,
                team=player.team.value,
                won=won,
                survived=player.alive,
                death_round=player.died_at_round,
                death_phase=player.died_at_phase.value if player.died_at_phase else None,
                death_reason=player.died_reason.value if player.died_reason else None,
                actions_count=_count_actions(state, player.user_id),
                successful_actions=_count_successful(state, player.user_id),
                received_votes=_count_votes_received(state, player.user_id),
                cast_votes=_count_votes_cast(state, player.user_id),
                afk_turns=player.skipped_phases,
                elo_before=global_change.elo_before,
                elo_after=global_change.elo_after,
                elo_change=global_change.delta,
                xp_earned=xp_earned,
                dollars_earned=dollars_earned,
                game_duration_seconds=duration,
                game_player_count=len(state.players),
                played_at=game.finished_at or game.started_at,
            )

            # 2. UserStats UPDATE (incremental)
            await _update_user_stats(player, won, xp_earned, dollars_earned, global_change)

            # 3. GroupUserStats UPDATE
            await _update_group_user_stats(player, state.group_id, won, xp_earned, group_change)

            # 4. User balance + XP
            user = await User.get(id=player.user_id)
            user.xp += xp_earned
            user.dollars += dollars_earned
            user.level = _compute_level(user.xp)
            await user.save(update_fields=["xp", "dollars", "level"])

        # 5. GroupStats (rolling)
        await _update_group_stats(state, duration)

    # Achievement checks
    from app.services.achievement_service import check_and_unlock

    for player in state.players:
        user = await User.get_or_none(id=player.user_id)
        if user is not None:
            try:
                await check_and_unlock(user, state)
            except Exception as e:
                logger.warning(f"Achievement check for {user.id} failed: {e}")

    logger.info(f"Stats finalized for game {state.id}: winner={state.winner_team}")


def _count_actions(state: GameState, user_id: int) -> int:
    count = 0
    for round_log in state.rounds:
        for a in round_log.night_actions:
            if a.actor_id == user_id:
                count += 1
    return count


def _count_successful(state: GameState, user_id: int) -> int:
    """Heuristic: kill/check/heal/sleep that resulted in something."""
    count = 0
    for round_log in state.rounds:
        for a in round_log.night_actions:
            if a.actor_id != user_id:
                continue
            if (
                (a.action_type == "kill" and a.target_id in round_log.night_deaths)
                or (a.action_type == "heal" and a.target_id is not None)
                or a.action_type == "check"
                or a.action_type == "sleep"
            ):
                count += 1
    return count


def _count_votes_received(state: GameState, user_id: int) -> int:
    count = 0
    for round_log in state.rounds:
        for v in round_log.day_votes:
            if v.target_id == user_id:
                count += v.weight
    return count


def _count_votes_cast(state: GameState, user_id: int) -> int:
    count = 0
    for round_log in state.rounds:
        for v in round_log.day_votes:
            if v.voter_id == user_id:
                count += 1
    return count


async def _update_user_stats(
    player, won: bool, xp_earned: int, dollars_earned: int, elo_change: EloChange
) -> None:
    stats, _ = await UserStats.get_or_create(user_id=player.user_id)
    stats.games_total += 1
    if won:
        stats.games_won += 1
        stats.current_win_streak += 1
        stats.current_loss_streak = 0
        if stats.current_win_streak > stats.longest_win_streak:
            stats.longest_win_streak = stats.current_win_streak
    else:
        stats.games_lost += 1
        stats.current_loss_streak += 1
        stats.current_win_streak = 0

    # Team aggregate
    team_value = player.team.value
    if team_value == "citizens":
        stats.citizen_games += 1
        if won:
            stats.citizen_wins += 1
    elif team_value == "mafia":
        stats.mafia_games += 1
        if won:
            stats.mafia_wins += 1
    else:
        stats.singleton_games += 1
        if won:
            stats.singleton_wins += 1

    # Survival
    if player.alive:
        stats.times_survived += 1
    else:
        if player.died_reason == DeathReason.VOTED_OUT:
            stats.times_voted_out += 1
        elif player.died_at_phase == Phase.NIGHT:
            stats.times_killed_at_night += 1

    # Role stats JSON
    role_stats = stats.role_stats or {}
    role_entry = role_stats.get(player.role, {"games": 0, "wins": 0, "elo": 1000})
    role_entry["games"] = role_entry.get("games", 0) + 1
    if won:
        role_entry["wins"] = role_entry.get("wins", 0) + 1
    role_entry["winrate"] = (
        round(role_entry["wins"] / role_entry["games"], 3) if role_entry["games"] else 0
    )
    role_entry["elo"] = elo_change.elo_after
    role_stats[player.role] = role_entry
    stats.role_stats = role_stats

    # ELO/XP
    stats.elo = elo_change.elo_after
    stats.xp += xp_earned
    stats.level = _compute_level(stats.xp)
    stats.last_played_at = stats.last_played_at  # auto
    from datetime import datetime

    stats.last_played_at = datetime.now(UTC)

    await stats.save()


async def _update_group_user_stats(
    player, group_id: int, won: bool, xp_earned: int, elo_change: EloChange
) -> None:
    gus, _ = await GroupUserStats.get_or_create(user_id=player.user_id, group_id=group_id)
    gus.games_total += 1
    if won:
        gus.games_won += 1

    role_stats = gus.role_stats or {}
    role_entry = role_stats.get(player.role, {"games": 0, "wins": 0})
    role_entry["games"] += 1
    if won:
        role_entry["wins"] += 1
    role_entry["winrate"] = round(role_entry["wins"] / role_entry["games"], 3)
    role_stats[player.role] = role_entry
    gus.role_stats = role_stats

    gus.elo = elo_change.elo_after
    gus.xp += xp_earned
    from datetime import datetime

    gus.last_played_at = datetime.now(UTC)
    await gus.save()


async def _update_group_stats(state: GameState, duration: int) -> None:
    """Rolling avg group stats."""
    gs, _ = await GroupStats.get_or_create(group_id=state.group_id)
    n_old = gs.total_games
    gs.total_games += 1

    # Rolling averages
    gs.avg_game_duration_seconds = (
        gs.avg_game_duration_seconds * n_old + duration
    ) / gs.total_games
    gs.avg_player_count = (gs.avg_player_count * n_old + len(state.players)) / gs.total_games

    # Team winrates
    if state.winner_team == Team.CITIZENS:
        gs.citizens_winrate = (gs.citizens_winrate * n_old + 1.0) / gs.total_games
        gs.mafia_winrate = (gs.mafia_winrate * n_old + 0.0) / gs.total_games
    elif state.winner_team == Team.MAFIA:
        gs.mafia_winrate = (gs.mafia_winrate * n_old + 1.0) / gs.total_games
        gs.citizens_winrate = (gs.citizens_winrate * n_old + 0.0) / gs.total_games

    from datetime import datetime

    gs.last_game_at = datetime.now(UTC)
    await gs.save()


def _compute_level(xp: int) -> int:
    """Simple curve: lvl 1 at 0 XP, lvl 2 at 100, lvl 3 at 250, lvl N at N*(N+1)*50."""
    level = 1
    while xp >= level * (level + 1) * 50:
        level += 1
    return level
