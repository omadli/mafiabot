from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "system_settings" (
            "id" INT NOT NULL PRIMARY KEY,
            "item_prices" JSON NOT NULL DEFAULT '{}',
            "rewards" JSON NOT NULL DEFAULT '{}',
            "exchange" JSON NOT NULL DEFAULT '{}',
            "premium" JSON NOT NULL DEFAULT '{}',
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by_tg_id" BIGINT
        );"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "system_settings";"""
