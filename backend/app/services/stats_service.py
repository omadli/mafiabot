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
DOLLARS_LOSS = 2  # default for losers (winners use SystemSettings.rewards)


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
    duration_minutes = max(1, duration // 60)

    # Pre-compute reward (same for all winners of the same team)
    from app.services import pricing_service

    winner_team_value = state.winner_team.value if state.winner_team else None
    winner_dollars, _winner_xp_extra = await pricing_service.get_reward(
        duration_minutes=duration_minutes, winner_team=winner_team_value
    )

    async with in_transaction():
        for player in state.players:
            won = player.user_id in state.winner_user_ids
            global_change = elo_change_map.get(player.user_id)
            group_change = group_elo_map.get(player.user_id)
            if global_change is None or group_change is None:
                continue

            base_xp = XP_WIN if won else XP_LOSS
            xp_earned = base_xp + (XP_SURVIVED_BONUS if player.alive else 0)
            dollars_earned = winner_dollars if won else DOLLARS_LOSS

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

            # 5. Audit reward as Transaction (only for winners with positive amount)
            if won and dollars_earned > 0:
                from app.db.models import Transaction, TransactionStatus, TransactionType

                await Transaction.create(
                    user=user,
                    type=TransactionType.GAME_REWARD,
                    dollars_amount=dollars_earned,
                    status=TransactionStatus.COMPLETED,
                    note=(
                        f"game={state.id} duration={duration_minutes}min "
                        f"team={winner_team_value} role={player.role}"
                    ),
                )

        # 5. GroupStats (rolling)
        await _update_group_stats(state, duration)

    # Achievement checks + notifications
    from app.services.achievement_service import check_and_unlock, notify_unlock

    for player in state.players:
        user = await User.get_or_none(id=player.user_id)
        if user is None:
            continue
        try:
            unlocks = await check_and_unlock(user, state)
            if unlocks:
                from app.main import bot

                if bot is not None:
                    locale = user.language_code or "uz"
                    for ach in unlocks:
                        try:
                            await notify_unlock(bot, user.id, ach, locale)
                        except Exception as e:
                            logger.debug(f"Notify unlock failed for {user.id}: {e}")
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

    # ELO/XP
    new_elo = elo_change.elo_after
    new_xp = stats.xp + xp_earned
    new_level = _compute_level(new_xp)
    from datetime import datetime

    now = datetime.now(UTC)

    # Workaround: UserStats has OneToOneField(pk=True) which breaks
    # instance.save() on PostgreSQL (see group_settings_helper for details).
    # Use filter().update() with explicit column kwargs instead.
    await UserStats.filter(user_id=player.user_id).update(
        games_total=stats.games_total,
        games_won=stats.games_won,
        games_lost=stats.games_lost,
        current_win_streak=stats.current_win_streak,
        longest_win_streak=stats.longest_win_streak,
        current_loss_streak=stats.current_loss_streak,
        citizen_games=stats.citizen_games,
        citizen_wins=stats.citizen_wins,
        mafia_games=stats.mafia_games,
        mafia_wins=stats.mafia_wins,
        singleton_games=stats.singleton_games,
        singleton_wins=stats.singleton_wins,
        times_survived=stats.times_survived,
        times_killed_at_night=stats.times_killed_at_night,
        times_voted_out=stats.times_voted_out,
        role_stats=role_stats,
        elo=new_elo,
        xp=new_xp,
        level=new_level,
        last_played_at=now,
    )


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
    new_total = n_old + 1

    # Rolling averages
    new_avg_duration = (gs.avg_game_duration_seconds * n_old + duration) / new_total
    new_avg_player_count = (gs.avg_player_count * n_old + len(state.players)) / new_total

    # Team winrates
    new_citizens_winrate = gs.citizens_winrate
    new_mafia_winrate = gs.mafia_winrate
    if state.winner_team == Team.CITIZENS:
        new_citizens_winrate = (gs.citizens_winrate * n_old + 1.0) / new_total
        new_mafia_winrate = (gs.mafia_winrate * n_old + 0.0) / new_total
    elif state.winner_team == Team.MAFIA:
        new_mafia_winrate = (gs.mafia_winrate * n_old + 1.0) / new_total
        new_citizens_winrate = (gs.citizens_winrate * n_old + 0.0) / new_total

    from datetime import datetime

    # Workaround: GroupStats also uses OneToOneField(pk=True). Use
    # filter().update() instead of save() to avoid the column-name bug.
    await GroupStats.filter(group_id=state.group_id).update(
        total_games=new_total,
        avg_game_duration_seconds=new_avg_duration,
        avg_player_count=new_avg_player_count,
        citizens_winrate=new_citizens_winrate,
        mafia_winrate=new_mafia_winrate,
        last_game_at=datetime.now(UTC),
    )


def _compute_level(xp: int) -> int:
    """Simple curve: lvl 1 at 0 XP, lvl 2 at 100, lvl 3 at 250, lvl N at N*(N+1)*50."""
    level = 1
    while xp >= level * (level + 1) * 50:
        level += 1
    return level
