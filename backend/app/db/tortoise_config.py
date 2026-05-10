"""Tortoise ORM config — supports both PostgreSQL (production) and SQLite (local dev)."""

from app.config import settings

MODELS_MODULES = [
    "app.db.models.user",
    "app.db.models.group",
    "app.db.models.game",
    "app.db.models.statistics",
    "app.db.models.transaction",
    "app.db.models.audit",
    "app.db.models.system_settings",
    "aerich.models",
]

TORTOISE_ORM = {
    "connections": {
        "default": settings.db_url,
    },
    "apps": {
        "models": {
            "models": MODELS_MODULES,
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}
