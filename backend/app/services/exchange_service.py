"""Currency exchange — diamonds ↔ dollars.

Rate is configured in SystemSettings.exchange.diamond_to_dollar_rate.
Default: 1 💎 = 1000 💵.

Atomic: uses select_for_update to prevent race conditions.
"""

from __future__ import annotations

from loguru import logger
from tortoise.transactions import in_transaction

from app.db.models import Transaction, TransactionStatus, TransactionType, User
from app.services import pricing_service


class ExchangeError(Exception):
    pass


class ExchangeDisabled(ExchangeError):
    pass


class InsufficientBalance(ExchangeError):
    pass


class BelowMinimum(ExchangeError):
    pass


async def diamonds_to_dollars(user: User, diamonds: int) -> int:
    """Convert diamonds → dollars. Returns dollars credited."""
    if not await pricing_service.is_exchange_enabled():
        raise ExchangeDisabled("Currency exchange is disabled")

    min_amount = await pricing_service.get_exchange_min("diamonds")
    if diamonds < min_amount:
        raise BelowMinimum(f"Minimum {min_amount} 💎 to convert")

    rate = await pricing_service.get_diamond_to_dollar_rate()
    dollars = diamonds * rate

    async with in_transaction():
        u = await User.select_for_update().get(id=user.id)
        if u.diamonds < diamonds:
            raise InsufficientBalance(f"Need {diamonds} 💎, have {u.diamonds}")

        u.diamonds -= diamonds
        u.dollars += dollars
        await u.save(update_fields=["diamonds", "dollars"])

        await Transaction.create(
            user=u,
            type=TransactionType.EXCHANGE,
            diamonds_amount=-diamonds,
            dollars_amount=dollars,
            status=TransactionStatus.COMPLETED,
            note=f"diamonds→dollars @ {rate}",
        )

    logger.info(f"User {user.id} exchanged {diamonds}💎 → {dollars}💵")
    return dollars


async def dollars_to_diamonds(user: User, dollars: int) -> int:
    """Convert dollars → diamonds. Returns diamonds credited.

    Note: dollars are converted at the same rate (1💎 = N💵), so input
    must be a multiple of the rate to avoid rounding losses.
    """
    if not await pricing_service.is_exchange_enabled():
        raise ExchangeDisabled("Currency exchange is disabled")

    min_amount = await pricing_service.get_exchange_min("dollars")
    if dollars < min_amount:
        raise BelowMinimum(f"Minimum {min_amount} 💵 to convert")

    rate = await pricing_service.get_diamond_to_dollar_rate()
    if dollars % rate != 0:
        # Round down to nearest multiple to avoid rounding loss
        dollars = (dollars // rate) * rate
        if dollars == 0:
            raise BelowMinimum(f"Amount must be a multiple of {rate}")

    diamonds = dollars // rate

    async with in_transaction():
        u = await User.select_for_update().get(id=user.id)
        if u.dollars < dollars:
            raise InsufficientBalance(f"Need {dollars} 💵, have {u.dollars}")

        u.dollars -= dollars
        u.diamonds += diamonds
        await u.save(update_fields=["dollars", "diamonds"])

        await Transaction.create(
            user=u,
            type=TransactionType.EXCHANGE,
            diamonds_amount=diamonds,
            dollars_amount=-dollars,
            status=TransactionStatus.COMPLETED,
            note=f"dollars→diamonds @ {rate}",
        )

    logger.info(f"User {user.id} exchanged {dollars}💵 → {diamonds}💎")
    return diamonds
