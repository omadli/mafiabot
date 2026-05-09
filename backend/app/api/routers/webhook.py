"""Telegram webhook receiver."""

from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request

from app.config import settings

router = APIRouter()


@router.post("/{secret}")
async def telegram_webhook(secret: str, request: Request) -> dict:
    """Receive Telegram updates via webhook.

    URL: https://mafia.omadli.uz/webhook/{secret}
    """
    if secret != settings.webhook_secret.get_secret_value():
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    # Lazy import to avoid circular
    from app.main import bot, dp

    if bot is None or dp is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
