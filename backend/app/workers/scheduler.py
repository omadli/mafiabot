"""APScheduler — cron tasks for stats rollup, AFK ban cleanup, etc."""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.workers.stats_rollup import rollup_daily, rollup_monthly, rollup_weekly

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # Daily at 00:01
    _scheduler.add_job(
        rollup_daily,
        CronTrigger(hour=0, minute=1),
        name="rollup_daily",
        replace_existing=True,
        id="rollup_daily",
    )
    # Weekly Monday at 00:05
    _scheduler.add_job(
        rollup_weekly,
        CronTrigger(day_of_week="mon", hour=0, minute=5),
        name="rollup_weekly",
        replace_existing=True,
        id="rollup_weekly",
    )
    # Monthly 1st at 00:10
    _scheduler.add_job(
        rollup_monthly,
        CronTrigger(day=1, hour=0, minute=10),
        name="rollup_monthly",
        replace_existing=True,
        id="rollup_monthly",
    )

    _scheduler.start()
    logger.info("Scheduler started: rollup_daily, rollup_weekly, rollup_monthly")
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
