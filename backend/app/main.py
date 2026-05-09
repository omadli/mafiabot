"""Application entry point: FastAPI + aiogram bot.

Two modes:
    - webhook (production): bot updates via FastAPI /webhook
    - polling (local dev): bot polls via long polling, parallel with FastAPI

FSM storage:
    - redis (production): RedisStorage
    - memory (local dev): MemoryStorage

Database:
    - DATABASE_URL env var overrides postgres_dsn (e.g., sqlite://./mafia.db for local dev)
"""

import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

import sentry_sdk
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from fastapi import FastAPI
from loguru import logger
from sentry_sdk.integrations.fastapi import FastApiIntegration
from tortoise import Tortoise

from app.config import settings
from app.db.tortoise_config import TORTOISE_ORM


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG" if settings.debug else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
        backtrace=settings.debug,
        diagnose=settings.debug,
    )


def setup_sentry() -> None:
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )
    logger.info("Sentry initialized")


def _build_storage() -> BaseStorage:
    """FSM storage tanlash: memory (local dev) yoki Redis (production)."""
    if settings.fsm_storage == "memory":
        logger.info("FSM storage: MemoryStorage (local dev)")
        return MemoryStorage()
    logger.info(f"FSM storage: RedisStorage ({settings.redis_url})")
    return RedisStorage.from_url(settings.redis_url)


async def init_db() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    if settings.database_url and settings.database_url.startswith("sqlite"):
        # Auto-create schema for local SQLite (no Aerich needed for dev)
        await Tortoise.generate_schemas(safe=True)
        logger.info(f"Database connected: {settings.database_url} (schema generated)")
    else:
        logger.info(f"Database connected: {settings.db_url.split('@')[-1]}")

    # Seed achievements
    try:
        from app.services.achievement_service import seed_achievements

        await seed_achievements()
    except Exception as e:
        logger.warning(f"Achievement seed failed: {e}")


async def close_db() -> None:
    await Tortoise.close_connections()
    logger.info("Database disconnected")


# Bot/dispatcher singletons
bot: Bot | None = None
dp: Dispatcher | None = None


async def setup_bot() -> tuple[Bot, Dispatcher]:
    global bot, dp

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=_build_storage())

    from app.bot.dispatcher import setup_routers

    setup_routers(dp)
    logger.info(f"Bot initialized: mode={settings.bot_mode}, env={settings.environment}")
    return bot, dp


async def _start_webhook(bot_instance: Bot, dp_instance: Dispatcher) -> None:
    """Production: webhook orqali Telegram update'lar qabul qilish."""
    webhook_info = await bot_instance.get_webhook_info()
    if webhook_info.url != settings.webhook_url:
        await bot_instance.set_webhook(
            url=settings.webhook_url,
            allowed_updates=dp_instance.resolve_used_update_types(),
            drop_pending_updates=True,
        )
        logger.info(f"Webhook set to {settings.webhook_url}")


async def _start_polling_task(bot_instance: Bot, dp_instance: Dispatcher) -> asyncio.Task:
    """Local dev: long polling parallel asyncio task."""
    # Delete webhook first (Telegram requires polling without webhook)
    try:
        await bot_instance.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted (polling mode)")
    except Exception as e:
        logger.warning(f"Could not delete webhook: {e}")

    task = asyncio.create_task(dp_instance.start_polling(bot_instance, handle_signals=False))
    logger.info("Bot polling started")
    return task


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    setup_sentry()
    await init_db()
    bot_instance, dp_instance = await setup_bot()

    polling_task: asyncio.Task | None = None
    if settings.bot_mode == "webhook":
        await _start_webhook(bot_instance, dp_instance)
    else:
        polling_task = await _start_polling_task(bot_instance, dp_instance)

    # Set bot commands menu (private + group scopes)
    from app.bot.handlers.common.help import setup_bot_commands

    await setup_bot_commands(bot_instance)

    # Start scheduler (cron: stats rollup)
    from app.workers.scheduler import shutdown_scheduler, start_scheduler

    start_scheduler()

    logger.info(f"Application startup complete (mode={settings.bot_mode})")
    yield

    shutdown_scheduler()
    if polling_task is not None:
        polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await polling_task
    await bot_instance.session.close()
    await close_db()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mafia Bot API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url=None,
    )

    from app.api.routers import admin, health, webhook, ws

    app.include_router(health.router, tags=["health"])
    app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
    app.include_router(admin.router, prefix="/api", tags=["admin"])
    app.include_router(ws.router, prefix="/ws", tags=["websocket"])

    # CORS for frontend dev server
    if settings.environment == "development":
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app


app = create_app()


def main() -> None:
    """Entry point for `python -m app.main`."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.debug,
        log_config=None,
    )


if __name__ == "__main__":
    main()
