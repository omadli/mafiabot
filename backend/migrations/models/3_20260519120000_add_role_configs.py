from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "role_configs" (
            "role" VARCHAR(32) NOT NULL PRIMARY KEY,
            "team" VARCHAR(16) NOT NULL,
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
        DROP TABLE IF EXISTS "role_configs";"""
