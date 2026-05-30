"""Add `system_settings.diamond_packages` JSONB column.

Moves the diamond-purchase tier list off the Python `payment_service`
module so the super-admin can edit prices / bonuses / stars cost at
runtime. The column is seeded with the previous hard-coded defaults
the first time `pricing_service.get_settings()` (or this migration)
runs so the shop keeps working with no manual reseed.

Shape of each entry:
    {"code": str, "diamonds": int, "bonus_diamonds": int,
     "stars_price": int, "display_order": int, "enabled": bool}
"""

import json

from tortoise import BaseDBAsyncClient

_SEED = [
    {
        "code": "pack_50",
        "diamonds": 50,
        "bonus_diamonds": 0,
        "stars_price": 50,
        "display_order": 10,
        "enabled": True,
    },
    {
        "code": "pack_150",
        "diamonds": 150,
        "bonus_diamonds": 15,
        "stars_price": 125,
        "display_order": 20,
        "enabled": True,
    },
    {
        "code": "pack_500",
        "diamonds": 500,
        "bonus_diamonds": 100,
        "stars_price": 400,
        "display_order": 30,
        "enabled": True,
    },
    {
        "code": "pack_1000",
        "diamonds": 1000,
        "bonus_diamonds": 250,
        "stars_price": 750,
        "display_order": 40,
        "enabled": True,
    },
]


async def upgrade(db: BaseDBAsyncClient) -> str:
    seed = json.dumps(_SEED)
    return f"""
        ALTER TABLE "system_settings"
            ADD COLUMN IF NOT EXISTS "diamond_packages" JSONB NOT NULL DEFAULT '[]'::jsonb;

        -- Backfill the singleton row with the previous hard-coded packages
        -- so the shop keeps rendering tiers immediately after deploy.
        UPDATE "system_settings"
            SET "diamond_packages" = '{seed}'::jsonb
            WHERE "id" = 1 AND ("diamond_packages" IS NULL OR jsonb_array_length("diamond_packages") = 0);
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "system_settings" DROP COLUMN IF EXISTS "diamond_packages";
    """
