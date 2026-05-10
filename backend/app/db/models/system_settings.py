"""SystemSettings — singleton row for super-admin tunable parameters.

All prices/rewards/exchange-rate values live here so they can be edited
at runtime via /sa_setprice and admin panel without redeploys.
"""

from __future__ import annotations

from typing import ClassVar

from tortoise import fields
from tortoise.models import Model

# === Default values (used to seed the row on first run) ===

DEFAULT_ITEM_PRICES: dict = {
    # Tinch tomon (dollar bilan sotilishi mumkin)
    "shield": {"dollars": 150, "diamonds": 0},
    "fake_document": {"dollars": 200, "diamonds": 0},
    # Premium himoyalar (faqat olmos)
    "killer_shield": {"dollars": 0, "diamonds": 1},
    "vote_shield": {"dollars": 0, "diamonds": 1},
    "rifle": {"dollars": 0, "diamonds": 1},
    "mask": {"dollars": 0, "diamonds": 1},
    "special_role": {"dollars": 0, "diamonds": 2},
}

DEFAULT_REWARDS: dict = {
    # Game-end dollar reward — by duration + winner team
    "win_short_dollars": 10,  # game < threshold minutes
    "win_long_dollars": 20,  # game >= threshold minutes
    "long_threshold_minutes": 2,
    "mafia_singleton_bonus": 30,  # extra dollars if winner is Mafia or Singleton
    # XP rewards
    "xp_per_game": 10,
    "xp_per_win": 25,
    "xp_per_survive": 5,
}

DEFAULT_EXCHANGE: dict = {
    "diamond_to_dollar_rate": 1000,  # 1 💎 = 1000 💵
    "enabled": True,
    "min_diamonds": 1,  # min 💎 to convert per transaction
    "min_dollars": 1000,  # min 💵 to convert per transaction
}

DEFAULT_PREMIUM: dict = {
    "monthly_diamonds": 200,
    "yearly_diamonds": 2000,
}


class SystemSettings(Model):
    """Single-row table storing tunable parameters.

    Always row id=1. Use `get_settings()` helper from `pricing_service` for cached access.
    """

    id = fields.IntField(pk=True)
    item_prices: dict = fields.JSONField(default=dict)
    rewards: dict = fields.JSONField(default=dict)
    exchange: dict = fields.JSONField(default=dict)
    premium: dict = fields.JSONField(default=dict)
    updated_at = fields.DatetimeField(auto_now=True)
    updated_by_tg_id = fields.BigIntField(null=True)  # who last changed

    class Meta:
        table = "system_settings"

    # Convenience defaults exposed for seeding
    DEFAULTS: ClassVar[dict] = {
        "item_prices": DEFAULT_ITEM_PRICES,
        "rewards": DEFAULT_REWARDS,
        "exchange": DEFAULT_EXCHANGE,
        "premium": DEFAULT_PREMIUM,
    }
