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
    diamonds_price: int
    inventory_field: str  # field in UserInventory to increment


# === Items purchasable with diamonds ===
ITEM_CATALOG: list[ItemSpec] = [
    ItemSpec(code="shield", diamonds_price=10, inventory_field="shield"),
    ItemSpec(code="killer_shield", diamonds_price=15, inventory_field="killer_shield"),
    ItemSpec(code="vote_shield", diamonds_price=12, inventory_field="vote_shield"),
    ItemSpec(code="rifle", diamonds_price=25, inventory_field="rifle"),
    ItemSpec(code="mask", diamonds_price=15, inventory_field="mask"),
    ItemSpec(code="fake_document", diamonds_price=20, inventory_field="fake_document"),
    ItemSpec(code="special_role", diamonds_price=50, inventory_field="special_role"),
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


async def purchase_item(user: User, item_code: str, quantity: int = 1) -> ItemSpec:
    """Buy an item with diamonds. Atomic."""
    spec = get_item(item_code)
    if spec is None:
        raise ValueError(f"Unknown item: {item_code}")
    if quantity < 1:
        raise ValueError("Quantity must be >= 1")

    cost = spec.diamonds_price * quantity

    async with in_transaction():
        user_locked = await User.select_for_update().get(id=user.id)
        if user_locked.diamonds < cost:
            raise InsufficientDiamonds(f"Need {cost} diamonds, have {user_locked.diamonds}")

        user_locked.diamonds -= cost
        await user_locked.save(update_fields=["diamonds"])

        # Increment inventory field
        inv, _ = await UserInventory.get_or_create(user=user_locked)
        current = getattr(inv, spec.inventory_field, 0)
        setattr(inv, spec.inventory_field, current + quantity)
        await inv.save(update_fields=[spec.inventory_field])

        await Transaction.create(
            user=user_locked,
            type=TransactionType.SPEND_DIAMONDS,
            diamonds_amount=-cost,
            item=item_code,
            status=TransactionStatus.COMPLETED,
            note=f"Quantity: {quantity}",
        )

    logger.info(f"User {user.id} bought {quantity}x {item_code} for {cost} diamonds")
    return spec


# === Premium subscription ===


PREMIUM_PRICE_MONTHLY = 200  # diamonds


async def buy_premium(user: User, days: int = 30) -> None:
    """Activate/extend premium for given days."""
    from datetime import datetime, timedelta

    cost = PREMIUM_PRICE_MONTHLY * (days // 30 or 1)

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
