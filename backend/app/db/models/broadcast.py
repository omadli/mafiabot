"""Super-admin broadcast tracking.

A `BroadcastRun` row is created the moment the SA picks Copy / Forward
in the bot's broadcast-prompt dialog. The background task then drives
the row forward through PENDING → RUNNING → COMPLETED (or FAILED) while
counting successes, recording failures, and marking blocked users
inactive. The SA inspects the final report via the admin panel or
gets a DM summary when the run finishes.

The `failed_users` JSONB stores per-recipient failure details:
    [{"user_id": 12345, "reason": "forbidden", "error_detail": "..."}]

These are kept inline (rather than a separate table) because a single
broadcast's failure list rarely exceeds a few thousand entries — well
under the JSONB practical limit — and queryability isn't a goal.
"""

from enum import StrEnum

from tortoise import fields
from tortoise.models import Model


class BroadcastMethod(StrEnum):
    """How the bot delivers each broadcast hop.

    `copy` uses Telegram's `copyMessage` API so users see the bot as the
    apparent sender (no "Forwarded from …" header). `forward` uses
    `forwardMessage` so the original author's name is preserved.
    """

    COPY = "copy"
    FORWARD = "forward"


class BroadcastStatus(StrEnum):
    """Lifecycle of a BroadcastRun row.

    The transition `RUNNING → INTERRUPTED` is set on app startup when
    a stale row is found (the previous backend died mid-broadcast). The
    operator can re-run from the dashboard; we don't auto-resume.
    """

    PENDING = "pending"  # row created, worker not yet started
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"  # task crashed; partial results in success/fail counts
    INTERRUPTED = "interrupted"  # backend died mid-run


class BroadcastRun(Model):
    """Single broadcast operation triggered by a super-admin."""

    id = fields.UUIDField(pk=True)

    # Who triggered it. Stored as raw Telegram ID rather than FK because
    # super-admins aren't required to have a User row.
    initiator_tg_id = fields.BigIntField()

    method = fields.CharEnumField(BroadcastMethod)
    # Source of the payload — typically the SA's private chat with the
    # bot and the forwarded message_id inside it. The bot replays this
    # via copy_message / forward_message for every recipient.
    source_chat_id = fields.BigIntField()
    source_message_id = fields.BigIntField()

    status = fields.CharEnumField(BroadcastStatus, default=BroadcastStatus.PENDING)

    # Audience snapshot at start. `total_users` is captured before the
    # send loop so progress reporting has a stable denominator even when
    # new users register mid-run.
    total_users = fields.IntField(default=0)
    success_count = fields.IntField(default=0)
    fail_count = fields.IntField(default=0)
    # Users whose status changed to inactive as a side-effect of this run.
    # Subset of fail_count — broken out for the final report.
    deactivated_count = fields.IntField(default=0)

    # Failure breakdown. Capped on write to keep the row payload bounded
    # at ~5k entries; everything beyond that is summarised by reason.
    failed_users: list = fields.JSONField(default=list)
    failure_summary: dict = fields.JSONField(default=dict)
    # {"forbidden": 12, "deactivated": 3, "bad_request": 1, "other": 0}

    # Whether the broadcast worker has already DMed the SA with the
    # final report. Survives restarts so the report isn't sent twice.
    report_delivered = fields.BooleanField(default=False)

    started_at = fields.DatetimeField(null=True)
    finished_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "broadcast_runs"
        indexes = [("status", "created_at")]

    def __str__(self) -> str:
        return (
            f"BroadcastRun({self.id}, method={self.method}, status={self.status}, "
            f"{self.success_count}/{self.total_users} ok)"
        )
