"""Stats period snapshot cron — daily/weekly/monthly aggregation from GameResult."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from loguru import logger

from app.db.models import GameResult, StatsPeriodSnapshot


async def rollup_daily(target_date: date | None = None) -> int:
    """Aggregate yesterday's GameResults into daily StatsPeriodSnapshot."""
    if target_date is None:
        target_date = (datetime.now(UTC) - timedelta(days=1)).date()

    period_start = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
    period_end = period_start + timedelta(days=1)

    return await _rollup_period("daily", target_date, target_date, period_start, period_end)


async def rollup_weekly(week_start: date | None = None) -> int:
    """Last completed week (Mon-Sun)."""
    if week_start is None:
        today = datetime.now(UTC).date()
        # Find Monday of last week
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        week_start = last_monday

    week_end = week_start + timedelta(days=6)
    period_start = datetime.combine(week_start, datetime.min.time(), tzinfo=UTC)
    period_end = period_start + timedelta(days=7)

    return await _rollup_period("weekly", week_start, week_end, period_start, period_end)


async def rollup_monthly(year: int | None = None, month: int | None = None) -> int:
    """Last completed month."""
    now = datetime.now(UTC)
    if year is None or month is None:
        first_of_this_month = date(now.year, now.month, 1)
        last_of_prev = first_of_this_month - timedelta(days=1)
        year = last_of_prev.year
        month = last_of_prev.month

    period_start_date = date(year, month, 1)
    period_end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    period_start = datetime.combine(period_start_date, datetime.min.time(), tzinfo=UTC)
    period_end = datetime.combine(period_end_date, datetime.min.time(), tzinfo=UTC)

    return await _rollup_period(
        "monthly",
        period_start_date,
        period_end_date - timedelta(days=1),
        period_start,
        period_end,
    )


async def _rollup_period(
    period: str,
    period_start_date: date,
    period_end_date: date,
    period_start: datetime,
    period_end: datetime,
) -> int:
    """Generic rollup logic. Aggregates per-user stats for given period."""
    # Group results by (user_id, group_id)
    results = await GameResult.filter(played_at__gte=period_start, played_at__lt=period_end).all()

    if not results:
        logger.info(f"No GameResults for {period} {period_start_date}..{period_end_date}")
        return 0

    # Build aggregates: (user_id, group_id) → {games, wins, role_stats, elo_delta, xp}
    agg: dict[tuple[int, int | None], dict] = {}

    for r in results:
        # Per-user-per-group
        key = (r.user_id, r.group_id)
        a = agg.setdefault(
            key,
            {
                "games": 0,
                "wins": 0,
                "role_stats": {},
                "elo_change": 0,
                "xp_earned": 0,
            },
        )
        a["games"] += 1
        if r.won:
            a["wins"] += 1
        rs = a["role_stats"].setdefault(r.role, {"games": 0, "wins": 0})
        rs["games"] += 1
        if r.won:
            rs["wins"] += 1
        a["elo_change"] += r.elo_change
        a["xp_earned"] += r.xp_earned

        # Also global aggregate (group_id = None)
        global_key = (r.user_id, None)
        ga = agg.setdefault(
            global_key,
            {"games": 0, "wins": 0, "role_stats": {}, "elo_change": 0, "xp_earned": 0},
        )
        ga["games"] += 1
        if r.won:
            ga["wins"] += 1
        gs = ga["role_stats"].setdefault(r.role, {"games": 0, "wins": 0})
        gs["games"] += 1
        if r.won:
            gs["wins"] += 1
        ga["elo_change"] += r.elo_change
        ga["xp_earned"] += r.xp_earned

    # Upsert snapshots
    count = 0
    for (user_id, group_id), data in agg.items():
        await StatsPeriodSnapshot.update_or_create(
            user_id=user_id,
            group_id=group_id,
            period=period,
            period_start=period_start_date,
            defaults={
                "period_end": period_end_date,
                "games_total": data["games"],
                "games_won": data["wins"],
                "role_stats": data["role_stats"],
                "elo_change": data["elo_change"],
                "xp_earned": data["xp_earned"],
            },
        )
        count += 1

    logger.info(f"Rolled up {period} for {period_start_date}..{period_end_date}: {count} snapshots")
    return count
