"""Per-code emoji config (scene / status / item / action / currency).

Sibling of `role_config_service` for non-role visual elements. Lookups
happen on every bot message — keep them in-process and cached.

Public API:
    await get_all_configs(force=False) -> dict[code, EmojiConfig]
    await get_config(code) -> EmojiConfig | None
    await update_config(code, *, by_tg_id, **fields) -> EmojiConfig
    await seed_default_emoji_configs() -> None
    emoji_html_sync(code, overrides=None) -> str | None
        '<tg-emoji emoji-id="...">FALLBACK</tg-emoji>' if a custom_emoji_id
        is configured for that code, otherwise plain Unicode.
"""

from __future__ import annotations

import time
from typing import Any

from loguru import logger

from app.db.models import EmojiConfig
from app.db.models.emoji_config import DEFAULT_EMOJI_CONFIGS

_CACHE_TTL_SECONDS = 60
_cache: dict[str, Any] = {"configs": None, "ts": 0.0}

EDITABLE_FIELDS: frozenset[str] = frozenset(
    {
        "category",
        "name_uz",
        "name_ru",
        "name_en",
        "static_emoji",
        "custom_emoji_id",
        "order_idx",
    }
)


async def get_all_configs(force: bool = False) -> dict[str, EmojiConfig]:
    """All emoji configs as {code: EmojiConfig}, cached for ~1 minute.

    Auto-seeds the table from `DEFAULT_EMOJI_CONFIGS` on first call.
    """
    now = time.time()
    if not force and _cache["configs"] and (now - _cache["ts"]) < _CACHE_TTL_SECONDS:
        return _cache["configs"]

    rows = await EmojiConfig.all()
    if not rows:
        for spec in DEFAULT_EMOJI_CONFIGS:
            await EmojiConfig.create(**spec)
        rows = await EmojiConfig.all()
        logger.info(f"EmojiConfig seeded with {len(rows)} defaults")

    _cache["configs"] = {r.code: r for r in rows}
    _cache["ts"] = now
    return _cache["configs"]


def invalidate_cache() -> None:
    _cache["configs"] = None
    _cache["ts"] = 0.0


async def get_config(code: str) -> EmojiConfig | None:
    configs = await get_all_configs()
    return configs.get(code)


async def update_config(
    code: str,
    *,
    by_tg_id: int | None = None,
    **fields: Any,
) -> EmojiConfig:
    unknown = set(fields) - EDITABLE_FIELDS
    if unknown:
        raise ValueError(f"Cannot edit fields: {sorted(unknown)}")

    cfg = await EmojiConfig.get_or_none(code=code)
    if cfg is None:
        raise ValueError(f"Unknown emoji code: {code!r}")

    for k, v in fields.items():
        setattr(cfg, k, v)
    cfg.updated_by_tg_id = by_tg_id
    await cfg.save(
        update_fields=[*fields.keys(), "updated_at", "updated_by_tg_id"],
    )
    invalidate_cache()
    logger.info(f"EmojiConfig[{code}] updated by tg_id={by_tg_id}: {fields}")
    return cfg


async def seed_default_emoji_configs() -> None:
    """Idempotent — first call seeds defaults if table is empty; warms cache."""
    await get_all_configs(force=True)


# --- Sync helpers (read from cache, used by translator) ---


def _coerce_override(value: object) -> tuple[str, str] | None:
    if isinstance(value, list | tuple) and len(value) == 2:
        cid, fb = value
        if isinstance(cid, str) and isinstance(fb, str) and fb:
            return cid, fb
    if isinstance(value, dict):
        cid = value.get("custom_id", "")
        fb = value.get("fallback") or value.get("emoji") or ""
        if isinstance(cid, str) and isinstance(fb, str) and fb:
            return cid, fb
    return None


def emoji_html_sync(code: str, overrides: dict | None = None) -> str | None:
    """Render `code`'s emoji as HTML — `<tg-emoji>` if custom, else Unicode.

    Returns None when the cache hasn't warmed yet so the translator can
    fall through to the literal in `.ftl`.
    """
    if _cache["configs"] is None:
        return None

    pair: tuple[str, str] | None = None
    if overrides and code in overrides:
        pair = _coerce_override(overrides[code])
    if pair is None:
        cfg = _cache["configs"].get(code)
        if cfg is None:
            return None
        pair = (cfg.custom_emoji_id or "", cfg.static_emoji)

    custom_id, fallback = pair
    if custom_id:
        return f'<tg-emoji emoji-id="{custom_id}">{fallback}</tg-emoji>'
    return fallback
