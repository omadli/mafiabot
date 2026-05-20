from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "achievements"
        ADD COLUMN IF NOT EXISTS "dollars_reward" INT NOT NULL DEFAULT 0;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "achievements"
        DROP COLUMN IF EXISTS "dollars_reward";"""
