from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "groups" ADD COLUMN IF NOT EXISTS "is_premium" BOOL NOT NULL DEFAULT FALSE;
        ALTER TABLE "groups" ADD COLUMN IF NOT EXISTS "premium_expires_at" TIMESTAMPTZ;
        CREATE INDEX IF NOT EXISTS "idx_groups_is_premium" ON "groups" ("is_premium");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_groups_is_premium";
        ALTER TABLE "groups" DROP COLUMN IF EXISTS "premium_expires_at";
        ALTER TABLE "groups" DROP COLUMN IF EXISTS "is_premium";"""
