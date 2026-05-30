"""DM notifications dispatched when the super-admin acts on a user.

Whenever an SA grants diamonds/premium, bans/unbans, or sends a direct
admin message, the affected user gets a Telegram DM letting them know.
Keeps the admin → user feedback loop visible without the user having
to refresh the bot menu.

All helpers are best-effort: if the bot can't DM (forbidden, blocked,
chat deleted, no bot instance during tests) the failure is logged at
debug level and the calling endpoint still returns 200. The audit log
already records the action itself.

i18n is fetched per call against the target user's `language_code` so
the message lands in the language they actually use. Falls back to "uz"
when the user has no language set or the key is missing in their locale.
"""

from __future__ import annotations

from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger

from app.db.models import User
from app.services.i18n_service import get_translator


def _bot() -> Bot | None:
    """Resolve the live aiogram Bot — None during tests / before startup."""
    from app.main import bot

    return bot


def _safe_locale(user: User) -> str:
    return (user.language_code or "uz") if hasattr(user, "language_code") else "uz"


async def _safe_send(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
    except TelegramForbiddenError:
        logger.debug(f"SA notification: user {user_id} blocked the bot, skipping")
    except Exception as e:
        logger.debug(f"SA notification DM to user {user_id} failed: {e}")


async def notify_diamonds_granted(user: User, amount: int) -> None:
    """DM the user that the super-admin gifted them diamonds."""
    bot = _bot()
    if bot is None:
        return
    t = get_translator(_safe_locale(user))
    text = t("sa-notify-diamonds-granted", amount=amount)
    await _safe_send(bot, user.id, text)  # type: ignore[arg-type]


async def notify_premium_granted(user: User, expires_at: datetime) -> None:
    """DM the user that premium was extended/added by the super-admin."""
    bot = _bot()
    if bot is None:
        return
    t = get_translator(_safe_locale(user))
    expires_label = expires_at.strftime("%Y-%m-%d %H:%M UTC")
    text = t("sa-notify-premium-granted", expires=expires_label)
    await _safe_send(bot, user.id, text)  # type: ignore[arg-type]


async def notify_banned(user: User, reason: str | None) -> None:
    """DM the user that they were banned (and optionally why)."""
    bot = _bot()
    if bot is None:
        return
    t = get_translator(_safe_locale(user))
    reason_label = (reason or "").strip() or "—"
    text = t("sa-notify-banned", reason=reason_label)
    await _safe_send(bot, user.id, text)  # type: ignore[arg-type]


async def notify_unbanned(user: User) -> None:
    """DM the user that the ban was lifted."""
    bot = _bot()
    if bot is None:
        return
    t = get_translator(_safe_locale(user))
    text = t("sa-notify-unbanned")
    await _safe_send(bot, user.id, text)  # type: ignore[arg-type]


async def notify_admin_message(user: User, text: str) -> None:
    """Deliver a free-form admin → user message via the bot.

    The text is wrapped with a fixed envelope so the user can tell it
    apart from organic bot output, and explicitly noted as no-reply.
    The body is HTML-escaped before insertion so admin formatting can't
    break the wrapper or inject unrelated HTML.
    """
    bot = _bot()
    if bot is None:
        return
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = get_translator(_safe_locale(user))
    rendered = t("sa-notify-admin-message", body=safe)
    await _safe_send(bot, user.id, rendered)  # type: ignore[arg-type]
