from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "system_settings" (
            "id" INT NOT NULL PRIMARY KEY,
            "item_prices" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "rewards" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "exchange" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "premium" JSONB NOT NULL DEFAULT '{}'::jsonb,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by_tg_id" BIGINT
        );"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "system_settings";"""
