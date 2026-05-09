"""Telegram Stars payment handler — pre_checkout + successful_payment."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery
from loguru import logger

from app.db.models import User
from app.services import payment_service
from app.services.i18n_service import Translator

router = Router(name="private_payment")


@router.callback_query(F.data.startswith("buy:diamonds:"))
async def callback_buy_diamonds(query: CallbackQuery, user: User, _: Translator, bot: Bot) -> None:
    """Send Stars invoice for diamond package."""
    if query.data is None or query.message is None:
        await query.answer()
        return
    code = query.data.split(":")[2]
    pkg = payment_service.get_package(code)
    if pkg is None:
        await query.answer("Invalid package", show_alert=True)
        return

    try:
        await payment_service.send_diamond_invoice(bot, query.message.chat.id, pkg)
        await query.answer()
    except Exception as e:
        logger.exception(f"Failed to send invoice: {e}")
        await query.answer("Error", show_alert=True)


@router.pre_checkout_query()
async def handle_pre_checkout(query: PreCheckoutQuery, bot: Bot) -> None:
    await payment_service.handle_pre_checkout(bot, query)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message, user: User, _: Translator) -> None:
    """Credit diamonds after Stars payment."""
    if message.successful_payment is None:
        return
    total = await payment_service.handle_successful_payment(user, message.successful_payment)
    if total > 0:
        await message.answer(_("payment-success", diamonds=total))
    else:
        await message.answer(_("payment-failed"))
