from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "group_settings" ADD COLUMN IF NOT EXISTS "atmosphere_media" JSONB NOT NULL DEFAULT '{}'::jsonb;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "group_settings" DROP COLUMN IF EXISTS "atmosphere_media";"""
