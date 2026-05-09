"""Super admin API — placeholder.

Bosqich 3 da to'liq qo'llanadi. Hozircha skeleton.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/admin/ping")
async def admin_ping() -> dict:
    """Placeholder — admin auth Bosqich 3 da."""
    return {"ok": True, "message": "Admin API skeleton — Bosqich 3 da to'liq"}
