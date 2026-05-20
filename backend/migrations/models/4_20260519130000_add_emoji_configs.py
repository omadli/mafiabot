from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "emoji_configs" (
            "code" VARCHAR(64) NOT NULL PRIMARY KEY,
            "category" VARCHAR(16) NOT NULL,
            "name_uz" VARCHAR(64) NOT NULL,
            "name_ru" VARCHAR(64) NOT NULL,
            "name_en" VARCHAR(64) NOT NULL,
            "static_emoji" VARCHAR(32) NOT NULL,
            "custom_emoji_id" VARCHAR(32) NOT NULL DEFAULT '',
            "order_idx" INT NOT NULL DEFAULT 0,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_by_tg_id" BIGINT
        );"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "emoji_configs";"""
