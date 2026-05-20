"""Per-role config (names + emojis) with in-process cache.

Reads dominate this table — every game message references at least one
role name/emoji — so we keep all 21 rows in memory and refresh every 60s
(or on explicit invalidation after a super-admin edit). Mirrors the
`pricing_service` pattern.

Public API:
    await get_all_configs(force=False) -> dict[role_slug, RoleConfig]
    await get_config(role) -> RoleConfig | None
    await update_config(role, *, by_tg_id, **fields) -> RoleConfig

Helpers for rendering messages (use these, not the raw model):
    await role_emoji_html(role, overrides=None) -> str
        '<tg-emoji emoji-id="…">FALLBACK</tg-emoji>' if custom_emoji_id is set,
        else the plain Unicode emoji.
    await role_label(role, lang, overrides=None) -> str
        'EMOJI NAME' — what you want to drop into Fluent messages or buttons.
    await role_name(role, lang, overrides=None) -> str
"""

from __future__ import annotations

import time
from typing import Any

from loguru import logger

from app.db.models import RoleConfig
from app.db.models.role_config import DEFAULT_ROLE_CONFIGS

_CACHE_TTL_SECONDS = 60
_cache: dict[str, Any] = {"configs": None, "ts": 0.0}

# Editable fields (whitelist for update_config + API patch handler).
EDITABLE_FIELDS: frozenset[str] = frozenset(
    {
        "team",
        "name_uz",
        "name_ru",
        "name_en",
        "static_emoji",
        "custom_emoji_id",
        "order_idx",
    }
)

SUPPORTED_LANGS: frozenset[str] = frozenset({"uz", "ru", "en"})


async def get_all_configs(force: bool = False) -> dict[str, RoleConfig]:
    """All role configs as {slug: RoleConfig}, cached for ~1 minute.

    Auto-seeds the table from `DEFAULT_ROLE_CONFIGS` on first call.
    """
    now = time.time()
    if not force and _cache["configs"] and (now - _cache["ts"]) < _CACHE_TTL_SECONDS:
        return _cache["configs"]

    rows = await RoleConfig.all()
    if not rows:
        # First boot — seed from DEFAULTS
        for spec in DEFAULT_ROLE_CONFIGS:
            await RoleConfig.create(**spec)
        rows = await RoleConfig.all()
        logger.info(f"RoleConfig seeded with {len(rows)} defaults")

    _cache["configs"] = {r.role: r for r in rows}
    _cache["ts"] = now
    return _cache["configs"]


def invalidate_cache() -> None:
    _cache["configs"] = None
    _cache["ts"] = 0.0


async def get_config(role: str) -> RoleConfig | None:
    configs = await get_all_configs()
    return configs.get(role)


async def update_config(
    role: str,
    *,
    by_tg_id: int | None = None,
    **fields: Any,
) -> RoleConfig:
    """Update one or more editable fields on a single role's config row."""
    unknown = set(fields) - EDITABLE_FIELDS
    if unknown:
        raise ValueError(f"Cannot edit fields: {sorted(unknown)}")

    cfg = await RoleConfig.get_or_none(role=role)
    if cfg is None:
        raise ValueError(f"Unknown role: {role!r}")

    for k, v in fields.items():
        setattr(cfg, k, v)
    cfg.updated_by_tg_id = by_tg_id
    await cfg.save(
        update_fields=[*fields.keys(), "updated_at", "updated_by_tg_id"],
    )
    invalidate_cache()
    logger.info(f"RoleConfig[{role}] updated by tg_id={by_tg_id}: {fields}")
    return cfg


async def seed_default_role_configs() -> None:
    """Idempotent: first call seeds defaults if table is empty; warms cache."""
    await get_all_configs(force=True)


# --- Rendering helpers ----------------------------------------------------


def _coerce_override(value: object) -> tuple[str, str] | None:
    """Normalise a per-group override entry to (custom_id, fallback)."""
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


def role_label_sync(
    role: str,
    lang: str,
    overrides: dict | None = None,
) -> str | None:
    """Synchronous lookup of '{emoji} {localised name}' from the in-memory cache.

    Returns None if the cache hasn't been warmed yet. Used by i18n_service's
    translator to short-circuit the static `.ftl` lookup for `role-{slug}`
    keys so super-admin edits propagate to every bot message without code
    changes at the callsites.
    """
    if _cache["configs"] is None:
        return None
    if lang not in SUPPORTED_LANGS:
        lang = "uz"

    pair: tuple[str, str] | None = None
    name: str | None = None
    if overrides and role in overrides:
        ov = overrides[role]
        # name override may live alongside the emoji override
        if isinstance(ov, dict):
            cand = ov.get(f"name_{lang}") or ov.get("name")
            if isinstance(cand, str) and cand:
                name = cand
        co = _coerce_override(ov)
        if co is not None:
            pair = co

    cfg = _cache["configs"].get(role)
    if cfg is None and pair is None:
        return None

    if pair is None and cfg is not None:
        pair = (cfg.custom_emoji_id or "", cfg.static_emoji)
    if name is None and cfg is not None:
        name = getattr(cfg, f"name_{lang}", cfg.name_uz)
    if name is None:
        name = role

    custom_id, fallback = pair if pair else ("", "")
    if custom_id:
        emoji_part = f'<tg-emoji emoji-id="{custom_id}">{fallback}</tg-emoji>'
    else:
        emoji_part = fallback
    return f"{emoji_part} {name}".strip()


async def role_emoji_html(role: str, overrides: dict | None = None) -> str:
    """HTML snippet that renders the role's emoji in a Telegram message.

    Per-group `overrides` (raw dict from `GroupSettings.misc["role_emojis"]`)
    take precedence over the global config.
    """
    pair: tuple[str, str] | None = None
    if overrides and role in overrides:
        pair = _coerce_override(overrides[role])
    if pair is None:
        cfg = await get_config(role)
        if cfg is None:
            return "❓"
        pair = (cfg.custom_emoji_id or "", cfg.static_emoji)

    custom_id, fallback = pair
    if custom_id:
        return f'<tg-emoji emoji-id="{custom_id}">{fallback}</tg-emoji>'
    return fallback


async def role_name(role: str, lang: str, overrides: dict | None = None) -> str:
    """Localised role display name (no emoji prefix)."""
    if lang not in SUPPORTED_LANGS:
        lang = "uz"
    if overrides and role in overrides:
        name_key = f"name_{lang}"
        if isinstance(overrides[role], dict) and overrides[role].get(name_key):
            return str(overrides[role][name_key])
    cfg = await get_config(role)
    if cfg is None:
        return role
    return getattr(cfg, f"name_{lang}", cfg.name_uz)


async def role_label(role: str, lang: str, overrides: dict | None = None) -> str:
    """'EMOJI NAME' — preferred shape for Fluent message arguments / buttons.

    Uses HTML emoji when a custom_emoji_id is set; otherwise plain Unicode.
    """
    emoji = await role_emoji_html(role, overrides)
    name = await role_name(role, lang, overrides)
    return f"{emoji} {name}"
