"""Healthcheck endpoint."""

from fastapi import APIRouter
from tortoise import Tortoise

from app import __version__

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Healthcheck for Docker/k8s and external monitors."""
    db_ok = False
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "version": __version__,
        "db": "ok" if db_ok else "fail",
    }
