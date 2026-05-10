from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py → backend/ → loyiha root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Loyiha root'idan qidirish (cwd qayerdan ishga tushirilganidan qat'i nazar)
        env_file=(_PROJECT_ROOT / ".env", _PROJECT_ROOT / ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Domain ===
    public_domain: str = "mafia.omadli.uz"

    # === Telegram ===
    bot_token: SecretStr
    bot_username: str = "MafGameUzBot"
    webhook_secret: SecretStr = Field(default=SecretStr("dev-secret"))
    webhook_base_url: str = "https://mafia.omadli.uz"

    # === Bot run mode ===
    bot_mode: Literal["polling", "webhook"] = "webhook"

    # === FSM storage ===
    fsm_storage: Literal["memory", "redis"] = "redis"

    # === Database ===
    # Override via DATABASE_URL (e.g., "sqlite://./mafia.db" or "postgres://...")
    database_url: str | None = None

    # PostgreSQL (used when DATABASE_URL not set)
    postgres_user: str = "mafia"
    postgres_password: SecretStr = Field(default=SecretStr("changeme"))
    postgres_db: str = "mafia"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # === Redis ===
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    # === Backend ===
    backend_port: int = 8000
    secret_key: SecretStr = Field(default=SecretStr("dev-secret-change-me"))
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "production"

    # === Super admin defaults ===
    admin_default_username: str = "admin"
    admin_default_password: SecretStr = Field(default=SecretStr("admin"))

    # Comma-separated Telegram user IDs of super admins (in-bot powers via /sa_*)
    super_admin_telegram_ids: str = ""

    @property
    def super_admin_ids(self) -> set[int]:
        """Parsed set of super admin Telegram user IDs."""
        out: set[int] = set()
        for part in self.super_admin_telegram_ids.split(","):
            part = part.strip()
            if part.lstrip("-").isdigit():
                out.add(int(part))
        return out

    # === Sentry ===
    sentry_dsn: str | None = None
    sentry_environment: str = "production"

    # === Backup ===
    backup_retention_days: int = 7

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgres://{self.postgres_user}:{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def db_url(self) -> str:
        """Effective database URL: DATABASE_URL override or postgres_dsn."""
        return self.database_url or self.postgres_dsn

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def webhook_path(self) -> str:
        return f"/webhook/{self.webhook_secret.get_secret_value()}"

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_base_url}{self.webhook_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
