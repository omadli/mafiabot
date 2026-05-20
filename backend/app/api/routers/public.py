"""Public, unauthenticated endpoints — used by the marketing landing page.

Mount under `/api/public/*`. Everything here is read-only and safe to expose:
no user data, no settings beyond presentation. Cached upstream by
`role_config_service` (60s TTL), so traffic from the landing page is
effectively free.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.services import role_config_service

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/role-configs")
async def public_role_configs() -> dict:
    """All roles with their name (3 langs) + emoji — for the landing roles section."""
    configs = await role_config_service.get_all_configs()
    items = sorted(configs.values(), key=lambda c: c.order_idx)
    return {
        "items": [
            {
                "role": c.role,
                "team": c.team,
                "name_uz": c.name_uz,
                "name_ru": c.name_ru,
                "name_en": c.name_en,
                "static_emoji": c.static_emoji,
                "custom_emoji_id": c.custom_emoji_id,
            }
            for c in items
        ]
    }
