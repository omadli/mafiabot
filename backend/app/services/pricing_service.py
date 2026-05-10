"""Pricing service — single source of truth for prices/rewards/exchange.

All values are stored in `SystemSettings` (singleton row, id=1) and cached
for 60 seconds. Super admins mutate via /sa_set* commands or admin panel.

Public API:
    await get_settings() -> SystemSettings
    await get_item_price(code) -> tuple[int, int]   # (dollars, diamonds)
    await get_reward(duration_minutes, winner_team) -> tuple[int, int]  # (dollars, xp)
    await get_diamond_to_dollar_rate() -> int
    await get_premium_price(days) -> int  # diamonds
    await update_setting(section, key, value, by_tg_id) -> None
    invalidate_cache()  # called after mutations
"""

from __future__ import annotations

import time
from typing import Any

from loguru import logger

from app.db.models import SystemSettings
from app.db.models.system_settings import (
    DEFAULT_EXCHANGE,
    DEFAULT_ITEM_PRICES,
    DEFAULT_PREMIUM,
    DEFAULT_REWARDS,
)

_CACHE_TTL_SECONDS = 60
_cache: dict[str, Any] = {"settings": None, "ts": 0.0}


async def get_settings(force: bool = False) -> SystemSettings:
    """Return cached SystemSettings (TTL 60s). Auto-creates if missing."""
    now = time.time()
    if not force and _cache["settings"] and (now - _cache["ts"]) < _CACHE_TTL_SECONDS:
        return _cache["settings"]

    s = await SystemSettings.get_or_none(id=1)
    if s is None:
        s = await SystemSettings.create(
            id=1,
            item_prices=DEFAULT_ITEM_PRICES.copy(),
            rewards=DEFAULT_REWARDS.copy(),
            exchange=DEFAULT_EXCHANGE.copy(),
            premium=DEFAULT_PREMIUM.copy(),
        )
        logger.info("SystemSettings row seeded with defaults")

    _cache["settings"] = s
    _cache["ts"] = now
    return s


def invalidate_cache() -> None:
    _cache["settings"] = None
    _cache["ts"] = 0.0


async def get_item_price(code: str) -> tuple[int, int]:
    """Returns (dollars, diamonds) for an item. (0, 0) if unknown."""
    s = await get_settings()
    spec = (s.item_prices or {}).get(code)
    if spec is None:
        spec = DEFAULT_ITEM_PRICES.get(code, {"dollars": 0, "diamonds": 0})
    return int(spec.get("dollars", 0)), int(spec.get("diamonds", 0))


async def get_reward(duration_minutes: int, winner_team: str | None) -> tuple[int, int]:
    """Returns (dollars, xp_extra) for a winning player.

    Rules:
    - duration < threshold → win_short_dollars
    - duration >= threshold → win_long_dollars
    - if winner is mafia or singleton → +mafia_singleton_bonus
    """
    s = await get_settings()
    r = s.rewards or DEFAULT_REWARDS

    threshold = int(r.get("long_threshold_minutes", 2))
    if duration_minutes >= threshold:
        dollars = int(r.get("win_long_dollars", 20))
    else:
        dollars = int(r.get("win_short_dollars", 10))

    if winner_team in ("mafia", "singleton"):
        dollars += int(r.get("mafia_singleton_bonus", 30))

    xp = int(r.get("xp_per_win", 25))
    return dollars, xp


async def get_diamond_to_dollar_rate() -> int:
    s = await get_settings()
    return int((s.exchange or DEFAULT_EXCHANGE).get("diamond_to_dollar_rate", 1000))


async def get_exchange_min(currency: str) -> int:
    """Min amount per single conversion (currency = 'diamonds'|'dollars')."""
    s = await get_settings()
    e = s.exchange or DEFAULT_EXCHANGE
    return int(e.get(f"min_{currency}", 1 if currency == "diamonds" else 1000))


async def is_exchange_enabled() -> bool:
    s = await get_settings()
    return bool((s.exchange or DEFAULT_EXCHANGE).get("enabled", True))


async def get_premium_price(days: int) -> int:
    """Diamonds price for premium of given days. 30→monthly, 365→yearly, else proportional."""
    s = await get_settings()
    p = s.premium or DEFAULT_PREMIUM
    monthly = int(p.get("monthly_diamonds", 200))
    yearly = int(p.get("yearly_diamonds", 2000))
    if days >= 365:
        return yearly
    if days >= 30:
        # Linear: 30→monthly, 60→2*monthly, etc.; capped at yearly
        return min(yearly, monthly * (days // 30))
    return monthly  # treat <30 days as 30


async def update_setting(section: str, key: str, value: Any, by_tg_id: int | None = None) -> None:
    """Update a single key inside a SystemSettings JSON section.

    section: one of 'item_prices', 'rewards', 'exchange', 'premium'
    key: the inner JSON key. For item_prices, key is 'shield.dollars' (dot notation).
    """
    s = await get_settings(force=True)
    if section not in ("item_prices", "rewards", "exchange", "premium"):
        raise ValueError(f"Unknown section: {section}")

    data = dict(getattr(s, section) or {})

    if section == "item_prices" and "." in key:
        item_code, currency = key.split(".", 1)
        item_data = dict(data.get(item_code, {"dollars": 0, "diamonds": 0}))
        item_data[currency] = int(value)
        data[item_code] = item_data
    else:
        data[key] = value

    setattr(s, section, data)
    s.updated_by_tg_id = by_tg_id
    await s.save(update_fields=[section, "updated_at", "updated_by_tg_id"])
    invalidate_cache()
    logger.info(f"SystemSettings updated: {section}.{key} = {value} by tg_id={by_tg_id}")


async def seed_default_settings() -> None:
    """Create the singleton row with defaults if not present."""
    await get_settings(force=True)
