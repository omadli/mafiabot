"""Telegram Stars (XTR) payment service — diamonds purchase + items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC

from aiogram import Bot
from aiogram.types import LabeledPrice
from loguru import logger
from tortoise.transactions import in_transaction

from app.db.models import Transaction, TransactionStatus, TransactionType, User, UserInventory


@dataclass
class DiamondPackage:
    code: str
    diamonds: int
    stars_price: int  # XTR (Telegram Stars)
    bonus_diamonds: int = 0


# === Diamond packages ===
DIAMOND_PACKAGES: list[DiamondPackage] = [
    DiamondPackage(code="pack_50", diamonds=50, stars_price=50),
    DiamondPackage(code="pack_150", diamonds=150, stars_price=125, bonus_diamonds=15),
    DiamondPackage(code="pack_500", diamonds=500, stars_price=400, bonus_diamonds=100),
    DiamondPackage(code="pack_1000", diamonds=1000, stars_price=750, bonus_diamonds=250),
]


@dataclass
class ItemSpec:
    code: str
    inventory_field: str  # field in UserInventory to increment


# === Items purchasable in shop (price comes from SystemSettings now) ===
ITEM_CATALOG: list[ItemSpec] = [
    ItemSpec(code="shield", inventory_field="shield"),
    ItemSpec(code="killer_shield", inventory_field="killer_shield"),
    ItemSpec(code="vote_shield", inventory_field="vote_shield"),
    ItemSpec(code="rifle", inventory_field="rifle"),
    ItemSpec(code="mask", inventory_field="mask"),
    ItemSpec(code="fake_document", inventory_field="fake_document"),
    ItemSpec(code="special_role", inventory_field="special_role"),
]


def get_package(code: str) -> DiamondPackage | None:
    return next((p for p in DIAMOND_PACKAGES if p.code == code), None)


def get_item(code: str) -> ItemSpec | None:
    return next((it for it in ITEM_CATALOG if it.code == code), None)


# === Diamond purchase via Telegram Stars ===


async def send_diamond_invoice(bot: Bot, chat_id: int, package: DiamondPackage) -> None:
    """Send Telegram Stars invoice for diamond package."""
    total_diamonds = package.diamonds + package.bonus_diamonds
    title = f"💎 {total_diamonds} olmos"
    description = f"{package.diamonds} olmos"
    if package.bonus_diamonds:
        description += f" + 🎁 {package.bonus_diamonds} bonus"

    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=f"diamonds:{package.code}",
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=title, amount=package.stars_price)],
        provider_token="",  # empty for XTR
        start_parameter=f"buy_{package.code}",
    )


async def handle_pre_checkout(bot: Bot, query) -> None:
    """Approve pre-checkout (validate payload)."""
    payload = query.invoice_payload
    if not payload.startswith("diamonds:"):
        await bot.answer_pre_checkout_query(query.id, ok=False, error_message="Invalid invoice")
        return
    code = payload.split(":", 1)[1]
    if get_package(code) is None:
        await bot.answer_pre_checkout_query(query.id, ok=False, error_message="Unknown package")
        return
    await bot.answer_pre_checkout_query(query.id, ok=True)


async def handle_successful_payment(user: User, payment_info) -> int:
    """Credit diamonds + record transaction. Returns total diamonds added."""
    payload = payment_info.invoice_payload
    if not payload.startswith("diamonds:"):
        logger.warning(f"Unknown payment payload: {payload}")
        return 0

    code = payload.split(":", 1)[1]
    pkg = get_package(code)
    if pkg is None:
        return 0

    total = pkg.diamonds + pkg.bonus_diamonds

    async with in_transaction():
        user.diamonds += total
        await user.save(update_fields=["diamonds"])

        await Transaction.create(
            user=user,
            type=TransactionType.BUY_DIAMONDS,
            stars_amount=pkg.stars_price,
            diamonds_amount=total,
            telegram_payment_charge_id=payment_info.telegram_payment_charge_id,
            status=TransactionStatus.COMPLETED,
            note=f"Package: {code}",
        )

    logger.info(f"User {user.id} bought {total} diamonds for {pkg.stars_price} stars")
    return total


# === Item purchase with diamonds ===


class InsufficientDiamonds(Exception):
    pass


class InsufficientDollars(Exception):
    pass


async def purchase_item(
    user: User, item_code: str, quantity: int = 1, currency: str | None = None
) -> tuple[ItemSpec, str, int]:
    """Buy an item using whichever currency the price is set in.

    If both dollars and diamonds prices are set, `currency` arg picks one.
    If neither is set (price = 0), raises ValueError.

    Returns (spec, currency_used, total_cost).
    """
    from app.services import pricing_service

    spec = get_item(item_code)
    if spec is None:
        raise ValueError(f"Unknown item: {item_code}")
    if quantity < 1:
        raise ValueError("Quantity must be >= 1")

    dollars_price, diamonds_price = await pricing_service.get_item_price(item_code)

    # Currency resolution: explicit arg > diamonds > dollars
    if currency is None:
        if diamonds_price > 0:
            currency = "diamonds"
        elif dollars_price > 0:
            currency = "dollars"
        else:
            raise ValueError(f"No price configured for item: {item_code}")
    elif currency == "diamonds" and diamonds_price <= 0:
        raise ValueError(f"{item_code} cannot be purchased with diamonds")
    elif currency == "dollars" and dollars_price <= 0:
        raise ValueError(f"{item_code} cannot be purchased with dollars")

    cost = (diamonds_price if currency == "diamonds" else dollars_price) * quantity

    async with in_transaction():
        user_locked = await User.select_for_update().get(id=user.id)

        if currency == "diamonds":
            if user_locked.diamonds < cost:
                raise InsufficientDiamonds(f"Need {cost} 💎, have {user_locked.diamonds}")
            user_locked.diamonds -= cost
            tx_type = TransactionType.SPEND_DIAMONDS
            tx_amount = {"diamonds_amount": -cost}
        else:
            if user_locked.dollars < cost:
                raise InsufficientDollars(f"Need {cost} 💵, have {user_locked.dollars}")
            user_locked.dollars -= cost
            tx_type = TransactionType.SPEND_DOLLARS
            tx_amount = {"dollars_amount": -cost}

        await user_locked.save(update_fields=[currency])

        # Increment inventory field.
        # UserInventory has OneToOneField(pk=True) which breaks
        # `inv.save()` on PostgreSQL (Tortoise 0.21 emits the field
        # name "user" instead of the column "user_id"). Use
        # filter().update() with the explicit column kwarg instead.
        inv, _ = await UserInventory.get_or_create(user=user_locked)
        current = getattr(inv, spec.inventory_field, 0)
        new_qty = current + quantity
        setattr(inv, spec.inventory_field, new_qty)
        await UserInventory.filter(user_id=user_locked.id).update(**{spec.inventory_field: new_qty})

        await Transaction.create(
            user=user_locked,
            type=tx_type,
            item=item_code,
            status=TransactionStatus.COMPLETED,
            note=f"Quantity: {quantity}, currency: {currency}",
            **tx_amount,
        )

    logger.info(f"User {user.id} bought {quantity}x {item_code} for {cost} {currency}")
    return spec, currency, cost


# === Premium subscription ===


PREMIUM_PRICE_MONTHLY = 200  # diamonds (legacy fallback; real value in SystemSettings)


async def buy_premium(user: User, days: int = 30) -> None:
    """Activate/extend premium for given days."""
    from datetime import datetime, timedelta

    from app.services import pricing_service

    cost = await pricing_service.get_premium_price(days)

    async with in_transaction():
        user_locked = await User.select_for_update().get(id=user.id)
        if user_locked.diamonds < cost:
            raise InsufficientDiamonds(f"Need {cost} diamonds")

        user_locked.diamonds -= cost
        now = datetime.now(UTC)
        if user_locked.premium_expires_at and user_locked.premium_expires_at > now:
            user_locked.premium_expires_at = user_locked.premium_expires_at + timedelta(days=days)
        else:
            user_locked.premium_expires_at = now + timedelta(days=days)
        user_locked.is_premium = True
        await user_locked.save(update_fields=["diamonds", "premium_expires_at", "is_premium"])

        await Transaction.create(
            user=user_locked,
            type=TransactionType.SPEND_DIAMONDS,
            diamonds_amount=-cost,
            item="premium",
            status=TransactionStatus.COMPLETED,
            note=f"Days: {days}",
        )

    logger.info(f"User {user.id} purchased premium ({days} days) for {cost} diamonds")
