"""Long-running broadcast worker.

The super-admin forwards (or simply sends) a message to the bot in
private chat, then taps Copy or Forward in the broadcast-prompt
dialog. That click creates a `BroadcastRun` row and schedules
`start_broadcast(run_id)` as an asyncio task. The task:

  1. Loads the candidate audience (`User.is_active=True`).
  2. Iterates them one at a time at `DEFAULT_DELAY_SECONDS` pace
     using `paced_gather` -- well below Telegram's 30 msg/s bot-wide
     cap with enough headroom for in-flight game traffic.
  3. Per-send failures are classified by `safe_messaging` and
     accumulated into the run's `failed_users` / `failure_summary`
     fields. `forbidden` and `deactivated` errors also flip
     `User.is_active = False` (done inside `safe_send`).
  4. Persists progress every `_PROGRESS_FLUSH_EVERY` users so the
     dashboard / a refreshed SA view show live counts.
  5. On completion, DMs the initiator with the success/fail/inactive
     totals and the top failure reasons.

Backend restart safety: a row left in `RUNNING` when the process
starts is flipped to `INTERRUPTED` by `recover_interrupted_runs()`
(called from app lifespan). The SA can re-run from the dashboard;
we don't auto-resume because the partially-delivered batch would
otherwise re-spam recipients who already got it.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from loguru import logger

from app.db.models import (
    BroadcastMethod,
    BroadcastRun,
    BroadcastStatus,
    User,
)
from app.services import safe_messaging

# How often we flush partial progress to the DB. Tuned so a 1k-user
# broadcast generates ~20 writes total -- light enough to barely show
# up in PG metrics, frequent enough that the dashboard's poll picks up
# meaningful progress.
_PROGRESS_FLUSH_EVERY = 50

# Hard cap on the per-row `failed_users` list. Beyond this we only
# update the `failure_summary` counters; the individual IDs aren't
# useful at that scale and risk bloating the JSONB column.
_MAX_FAILED_USERS_INLINE = 5000

# Strong references to in-flight broadcast tasks. Without this the
# event loop is free to GC the coroutine the moment `schedule_broadcast`
# returns; the `add_done_callback` discards on completion so the set
# tracks only live work.
_background_tasks: set[asyncio.Task] = set()


def _bot() -> Any | None:
    """Resolve the live aiogram Bot. None during tests / before startup."""
    from app.main import bot

    return bot


async def schedule_broadcast(
    *,
    initiator_tg_id: int,
    method: BroadcastMethod,
    source_chat_id: int,
    source_message_id: int,
) -> BroadcastRun:
    """Create the row + schedule the worker. Returns the row immediately.

    The endpoint / bot handler calls this and replies to the SA with the
    initial "Broadcast started -- N users queued" message based on the
    returned row.
    """
    run = await BroadcastRun.create(
        initiator_tg_id=initiator_tg_id,
        method=method,
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
        status=BroadcastStatus.PENDING,
    )
    # Detach the worker so the calling request returns fast. We track
    # the task only via the row's status; a dropped reference here is
    # fine because the event loop holds it through completion. The
    # module-level set keeps the linter / GC happy until the loop drops
    # the reference itself on coro completion.
    task = asyncio.create_task(_run_broadcast(run.id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    logger.info(
        f"Broadcast {run.id} scheduled by tg={initiator_tg_id} "
        f"(method={method.value}, source={source_chat_id}:{source_message_id})"
    )
    return run


async def recover_interrupted_runs() -> int:
    """Mark any RUNNING rows as INTERRUPTED on startup. Returns the count.

    Wired into the app lifespan so a row left RUNNING by a previous
    backend doesn't sit there forever. The SA sees the row labeled
    INTERRUPTED in the dashboard and can manually re-trigger.
    """
    n = await BroadcastRun.filter(status=BroadcastStatus.RUNNING).update(
        status=BroadcastStatus.INTERRUPTED,
        finished_at=datetime.now(UTC),
    )
    if n:
        logger.warning(f"recover_interrupted_runs: marked {n} stale broadcast rows as INTERRUPTED")
    return n


async def _run_broadcast(run_id: UUID) -> None:
    """Owned by `schedule_broadcast` -- runs to completion in the background."""
    run = await BroadcastRun.get_or_none(id=run_id)
    if run is None:
        logger.error(f"broadcast worker: run {run_id} vanished before start")
        return

    bot = _bot()
    if bot is None:
        # The endpoint should have prevented this, but never crash a
        # stuck worker -- mark FAILED so the dashboard can show it.
        run.status = BroadcastStatus.FAILED
        run.finished_at = datetime.now(UTC)
        await run.save()
        logger.error(f"broadcast {run_id}: bot not initialised, aborting")
        return

    run.status = BroadcastStatus.RUNNING
    run.started_at = datetime.now(UTC)
    await run.save()

    try:
        # Snapshot the audience at start so progress denominators stay
        # stable even if new users register during the run.
        rows = await User.filter(is_active=True, is_banned=False).values_list("id", flat=True)
        user_ids: list[int] = list(rows)  # type: ignore[arg-type]
        run.total_users = len(user_ids)
        await run.save(update_fields=["total_users"])
        logger.info(f"broadcast {run_id}: starting fan-out to {len(user_ids)} users")

        send_factory = _make_send_factory(
            bot, run.method, run.source_chat_id, run.source_message_id
        )

        success = 0
        failed_users: list[dict] = []
        failure_summary: dict[str, int] = {
            "forbidden": 0,
            "deactivated": 0,
            "bad_request": 0,
            "other": 0,
            "retry_after": 0,
        }
        deactivated = 0

        for idx, user_id in enumerate(user_ids):
            result = await safe_messaging.safe_send(
                send_factory(user_id),
                target_user_id=user_id,
            )
            if result.ok:
                success += 1
            else:
                reason = result.reason or "other"
                failure_summary[reason] = failure_summary.get(reason, 0) + 1
                if reason in ("forbidden", "deactivated"):
                    deactivated += 1
                if len(failed_users) < _MAX_FAILED_USERS_INLINE:
                    failed_users.append(
                        {
                            "user_id": user_id,
                            "reason": reason,
                            "error_detail": str(result.exc)[:200] if result.exc else None,
                        }
                    )

            # Persist progress periodically so the SA can see a live
            # count without us writing on every tick.
            if (idx + 1) % _PROGRESS_FLUSH_EVERY == 0:
                run.success_count = success
                run.fail_count = idx + 1 - success
                run.deactivated_count = deactivated
                run.failure_summary = failure_summary
                await run.save(
                    update_fields=[
                        "success_count",
                        "fail_count",
                        "deactivated_count",
                        "failure_summary",
                    ]
                )

            # Pace at 0.1 s between sends. Telegram bot-wide cap is
            # 30 msg/s; we sit at 10 msg/s with headroom for game
            # traffic running in parallel.
            await asyncio.sleep(safe_messaging.DEFAULT_DELAY_SECONDS)

        run.success_count = success
        run.fail_count = len(user_ids) - success
        run.deactivated_count = deactivated
        run.failure_summary = failure_summary
        run.failed_users = failed_users
        run.status = BroadcastStatus.COMPLETED
        run.finished_at = datetime.now(UTC)
        await run.save()
        logger.info(
            f"broadcast {run_id} complete: {success}/{len(user_ids)} ok, "
            f"{run.fail_count} failed, {deactivated} marked inactive"
        )

        await _report_to_initiator(run)
    except asyncio.CancelledError:
        # Lifespan shutdown -- mark interrupted, let `recover_interrupted_runs`
        # surface it on next start.
        await BroadcastRun.filter(id=run_id).update(
            status=BroadcastStatus.INTERRUPTED,
            finished_at=datetime.now(UTC),
        )
        logger.warning(f"broadcast {run_id} cancelled mid-run")
        raise
    except Exception as e:
        logger.exception(f"broadcast {run_id} crashed: {e}")
        await BroadcastRun.filter(id=run_id).update(
            status=BroadcastStatus.FAILED,
            finished_at=datetime.now(UTC),
        )


def _make_send_factory(
    bot: Any,
    method: BroadcastMethod,
    source_chat_id: int,
    source_message_id: int,
) -> Callable[[int], Callable[[], Awaitable[Any]]]:
    """Build a `user_id → coro_factory` closure for the chosen method.

    Returning a factory (not the awaitable) is what lets `safe_send`
    retry on 429: each invocation rebuilds a fresh coroutine.
    """
    if method == BroadcastMethod.COPY:

        def factory(user_id: int) -> Callable[[], Awaitable[Any]]:
            def _coro() -> Awaitable[Any]:
                return bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=source_chat_id,
                    message_id=source_message_id,
                )

            return _coro

        return factory

    def factory_fwd(user_id: int) -> Callable[[], Awaitable[Any]]:
        def _coro() -> Awaitable[Any]:
            return bot.forward_message(
                chat_id=user_id,
                from_chat_id=source_chat_id,
                message_id=source_message_id,
            )

        return _coro

    return factory_fwd


async def _report_to_initiator(run: BroadcastRun) -> None:
    """DM the SA with the final tally + top failure reasons."""
    if run.report_delivered:
        return
    bot = _bot()
    if bot is None:
        return
    duration = (
        (run.finished_at - run.started_at).total_seconds()
        if run.finished_at and run.started_at
        else 0
    )
    summary = run.failure_summary or {}
    summary_lines = [
        f"• {reason}: <b>{count}</b>" for reason, count in summary.items() if count > 0
    ]
    summary_block = "\n".join(summary_lines) if summary_lines else "—"

    # Resolve SA's language from their User row; fall back to "uz".
    from app.db.models import User
    from app.services.i18n_service import get_translator

    sa_user = await User.get_or_none(id=run.initiator_tg_id)
    locale = (
        (sa_user.language_code or "uz") if sa_user and hasattr(sa_user, "language_code") else "uz"
    )
    t = get_translator(locale)
    text = t(
        "sa-broadcast-report",
        method=run.method.value,
        total=run.total_users,
        success=run.success_count,
        fail=run.fail_count,
        deactivated=run.deactivated_count,
        duration=int(duration),
        summary=summary_block,
    )

    try:
        await bot.send_message(run.initiator_tg_id, text, parse_mode="HTML")
        run.report_delivered = True
        await run.save(update_fields=["report_delivered"])
    except Exception as e:  # pragma: no cover -- never block on a stuck DM
        logger.warning(f"broadcast {run.id}: final report DM failed: {e}")
