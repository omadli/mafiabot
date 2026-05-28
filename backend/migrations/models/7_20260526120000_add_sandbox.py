"""Add super-admin sandbox tables + defensive CHECK constraint on users.id.

Sandbox sessions and their bot-message transcripts live in two new
tables. Real users / games / stats are not touched.

The `users.id > 0` CHECK constraint is **defense in depth**: sandbox
fake users carry negative IDs (allocated in `app.core.sandbox_ids`) and
are only ever held in-memory by the user-loader middleware. The
constraint guarantees a hard DB-level failure if a sandbox ID ever
escapes its guards and reaches an INSERT — much easier to debug than
silent data corruption.
"""

from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "sandbox_sessions" (
            "id" UUID NOT NULL PRIMARY KEY,
            "created_at" TIMESTAMPTZ NOT NULL,
            "started_at" TIMESTAMPTZ,
            "finished_at" TIMESTAMPTZ,
            "status" VARCHAR(16) NOT NULL,
            "fake_group_id" BIGINT NOT NULL,
            "n_players" INT NOT NULL,
            "auto_play_mode" VARCHAR(16) NOT NULL,
            "timing_preset" VARCHAR(16) NOT NULL,
            "settings_snapshot" JSONB NOT NULL,
            "fake_users_snapshot" JSONB NOT NULL,
            "final_state" JSONB,
            "winner_team" VARCHAR(32),
            "transcript_summary" JSONB,
            "created_by_id" UUID NOT NULL REFERENCES "admin_accounts" ("id") ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS "idx_sandbox_sessions_creator_created"
            ON "sandbox_sessions" ("created_by_id", "created_at");
        CREATE INDEX IF NOT EXISTS "idx_sandbox_sessions_status"
            ON "sandbox_sessions" ("status");

        CREATE TABLE IF NOT EXISTS "sandbox_transcript_entries" (
            "id" BIGSERIAL NOT NULL PRIMARY KEY,
            "seq" INT NOT NULL,
            "ts" TIMESTAMPTZ NOT NULL,
            "type" VARCHAR(16) NOT NULL,
            "scope" VARCHAR(16) NOT NULL,
            "chat_id" BIGINT NOT NULL,
            "target_user_id" BIGINT,
            "message_id" INT NOT NULL,
            "ref_message_id" INT,
            "text" TEXT,
            "parse_mode" VARCHAR(32),
            "reply_markup" JSONB,
            "media" JSONB,
            "session_id" UUID NOT NULL REFERENCES "sandbox_sessions" ("id") ON DELETE CASCADE,
            CONSTRAINT "uq_sandbox_transcript_session_seq" UNIQUE ("session_id", "seq")
        );
        CREATE INDEX IF NOT EXISTS "idx_sandbox_transcript_session_seq"
            ON "sandbox_transcript_entries" ("session_id", "seq");

        ALTER TABLE "users"
            ADD CONSTRAINT "ck_users_id_positive"
            CHECK ("id" > 0) NOT VALID;
        ALTER TABLE "users" VALIDATE CONSTRAINT "ck_users_id_positive";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" DROP CONSTRAINT IF EXISTS "ck_users_id_positive";
        DROP TABLE IF EXISTS "sandbox_transcript_entries";
        DROP INDEX IF EXISTS "idx_sandbox_sessions_status";
        DROP INDEX IF EXISTS "idx_sandbox_sessions_creator_created";
        DROP TABLE IF EXISTS "sandbox_sessions";"""
