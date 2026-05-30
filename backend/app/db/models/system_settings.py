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
    # Group premium — separate price (typically higher than user premium)
    "group_monthly_diamonds": 1000,
    "group_yearly_diamonds": 10000,
    # Reward multiplier applied to dollar/diamond payouts at game end
    # when the host group is premium. 2.0 = double rewards.
    "group_reward_multiplier": 2.0,
}

# === Diamond packages (Telegram Stars purchase tiers) ===
#
# Each tier: `code` (stable identifier referenced by the Stars invoice
# payload), `diamonds` (BASE amount), `stars_price` (XTR cost),
# `bonus_diamonds` (extra granted on top of base — used as the "🎁+N"
# label in the shop). Total credited = diamonds + bonus_diamonds.
#
# The shop UI displays "{diamonds} 🎁+{bonus} — ⭐ {price}" so the
# buyer reads "150 base + 15 bonus for 125 stars" rather than the old
# (buggy) "{base+bonus} 🎁+{bonus}" form which double-counted the
# bonus in the lead number.
#
# `display_order` controls top-to-bottom listing — lower first.
DEFAULT_DIAMOND_PACKAGES: list[dict] = [
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


class SystemSettings(Model):
    """Single-row table storing tunable parameters.

    Always row id=1. Use `get_settings()` helper from `pricing_service` for cached access.
    """

    id = fields.IntField(pk=True)
    item_prices: dict = fields.JSONField(default=dict)
    rewards: dict = fields.JSONField(default=dict)
    exchange: dict = fields.JSONField(default=dict)
    premium: dict = fields.JSONField(default=dict)
    # Stars diamond-purchase tiers — see DEFAULT_DIAMOND_PACKAGES above
    # for shape. List (ordered) of {code, diamonds, bonus_diamonds,
    # stars_price, display_order, enabled} dicts.
    diamond_packages: list = fields.JSONField(default=list)
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
        "diamond_packages": DEFAULT_DIAMOND_PACKAGES,
    }
