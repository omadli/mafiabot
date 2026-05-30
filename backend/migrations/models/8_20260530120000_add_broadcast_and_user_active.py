"""Add `broadcast_runs` table + `users.is_active` reachability flag.

The broadcast feature lives at the bot-tier: the super-admin forwards
or copies a message to the bot in private chat, the bot fans it out
across every active user. Each operation gets its own `broadcast_runs`
row so progress, failure breakdown, and the final SA report are
durable across backend restarts.

`users.is_active` is the simple reachability marker the broadcast and
all paced bot-sends honour: when a send fails with TelegramForbidden
or "user is deactivated", we flip it to False so future runs skip the
recipient without burning a request slot on a guaranteed 403. The
flag is set back to True only when the user themselves interacts with
the bot again (handled in the start handler).
"""

from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users"
            ADD COLUMN IF NOT EXISTS "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS "inactive_reason" VARCHAR(128),
            ADD COLUMN IF NOT EXISTS "inactive_at" TIMESTAMPTZ;

        CREATE TABLE IF NOT EXISTS "broadcast_runs" (
            "id" UUID NOT NULL PRIMARY KEY,
            "initiator_tg_id" BIGINT NOT NULL,
            "method" VARCHAR(16) NOT NULL,
            "source_chat_id" BIGINT NOT NULL,
            "source_message_id" BIGINT NOT NULL,
            "status" VARCHAR(16) NOT NULL DEFAULT 'pending',
            "total_users" INT NOT NULL DEFAULT 0,
            "success_count" INT NOT NULL DEFAULT 0,
            "fail_count" INT NOT NULL DEFAULT 0,
            "deactivated_count" INT NOT NULL DEFAULT 0,
            "failed_users" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "failure_summary" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "report_delivered" BOOLEAN NOT NULL DEFAULT FALSE,
            "started_at" TIMESTAMPTZ,
            "finished_at" TIMESTAMPTZ,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS "broadcast_runs_status_created_idx"
            ON "broadcast_runs" ("status", "created_at");
        CREATE INDEX IF NOT EXISTS "users_is_active_idx"
            ON "users" ("is_active") WHERE "is_active" = TRUE;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "users_is_active_idx";
        DROP INDEX IF EXISTS "broadcast_runs_status_created_idx";
        DROP TABLE IF EXISTS "broadcast_runs";

        ALTER TABLE "users"
            DROP COLUMN IF EXISTS "inactive_at",
            DROP COLUMN IF EXISTS "inactive_reason",
            DROP COLUMN IF EXISTS "is_active";
    """
