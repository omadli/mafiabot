"""/profile, /inventory, /buy commands — private chat."""

from __future__ import annotations

import contextlib

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.db.models import User, UserInventory
from app.services import payment_service
from app.services.i18n_service import Translator

router = Router(name="private_inventory")
router.message.filter(F.chat.type == "private")

ITEM_LABELS = {
    "shield": "🛡 Himoya",
    "killer_shield": "⛑ Qotildan himoya",
    "vote_shield": "⚖️ Ovoz himoyasi",
    "rifle": "🔫 Miltiq",
    "mask": "🎭 Maska",
    "fake_document": "📁 Soxta hujjat",
    "special_role": "🃏 Maxsus rol",
}


@router.message(Command("profile"))
async def cmd_profile(message: Message, user: User, _: Translator) -> None:
    """Foydalanuvchi profili: balans, premium, level."""
    text = _(
        "profile-info",
        name=user.first_name,
        diamonds=user.diamonds,
        dollars=user.dollars,
        xp=user.xp,
        level=user.level,
        is_premium="✅" if user.is_premium else "❌",
        premium_until=(
            user.premium_expires_at.strftime("%Y-%m-%d") if user.premium_expires_at else "—"
        ),
    )
    await message.answer(text)


@router.message(Command("inventory", "items"))
async def cmd_inventory(message: Message, user: User, _: Translator) -> None:
    """Foydalanuvchining qurol/himoyalari + yoqish/o'chirish menyusi."""
    inv, _new = await UserInventory.get_or_create(user=user)
    settings = inv.settings or {}

    lines = [_("inventory-header")]
    keyboard_rows: list[list[InlineKeyboardButton]] = []

    for code, label in ITEM_LABELS.items():
        qty = getattr(inv, code, 0)
        item_settings = settings.get(code, {})
        enabled = item_settings.get("enabled", False)
        toggle = "✅" if enabled else "⬜"
        lines.append(f"{label}: <b>{qty}</b> {toggle}")
        keyboard_rows.append(
            [
                InlineKeyboardButton(
                    text=f"{toggle} {label}",
                    callback_data=f"inv:toggle:{code}",
                )
            ]
        )

    keyboard_rows.append([InlineKeyboardButton(text=_("btn-shop"), callback_data="shop:open")])
    await message.answer(
        "\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    )


@router.callback_query(F.data.startswith("inv:toggle:"))
async def callback_toggle_item(query: CallbackQuery, user: User, _: Translator) -> None:
    if query.data is None:
        await query.answer()
        return
    code = query.data.split(":")[2]
    if code not in ITEM_LABELS:
        await query.answer("Invalid", show_alert=True)
        return

    inv, _new = await UserInventory.get_or_create(user=user)
    settings = inv.settings or {}
    item_s = settings.get(code, {"enabled": False})
    item_s["enabled"] = not item_s.get("enabled", False)
    settings[code] = item_s
    inv.settings = settings
    await inv.save(update_fields=["settings"])

    state_text = _("inv-toggle-on") if item_s["enabled"] else _("inv-toggle-off")
    await query.answer(f"{ITEM_LABELS[code]}: {state_text}", show_alert=False)

    # Refresh menu
    if query.message:
        with contextlib.suppress(Exception):
            await cmd_inventory(query.message, user, _)


# === Shop ===


@router.callback_query(F.data == "shop:open")
async def callback_shop(query: CallbackQuery, user: User, _: Translator) -> None:
    """Show shop categories."""
    if query.message is None:
        await query.answer()
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("btn-buy-diamonds"), callback_data="shop:diamonds")],
            [InlineKeyboardButton(text=_("btn-buy-items"), callback_data="shop:items")],
            [InlineKeyboardButton(text=_("btn-buy-premium"), callback_data="shop:premium")],
            [InlineKeyboardButton(text=_("btn-back"), callback_data="shop:close")],
        ]
    )
    await query.message.edit_text(_("shop-welcome"), reply_markup=keyboard)
    await query.answer()


@router.callback_query(F.data == "shop:diamonds")
async def callback_shop_diamonds(query: CallbackQuery, user: User, _: Translator) -> None:
    rows = []
    for pkg in payment_service.DIAMOND_PACKAGES:
        total = pkg.diamonds + pkg.bonus_diamonds
        bonus_label = f" 🎁+{pkg.bonus_diamonds}" if pkg.bonus_diamonds else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💎 {total}{bonus_label} — ⭐ {pkg.stars_price}",
                    callback_data=f"buy:diamonds:{pkg.code}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data="shop:open")])
    if query.message:
        await query.message.edit_text(
            _("shop-diamonds-header"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
        )
    await query.answer()


@router.callback_query(F.data == "shop:items")
async def callback_shop_items(query: CallbackQuery, user: User, _: Translator) -> None:
    rows = []
    for spec in payment_service.ITEM_CATALOG:
        label = ITEM_LABELS.get(spec.code, spec.code)
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{label} — 💎 {spec.diamonds_price}",
                    callback_data=f"buy:item:{spec.code}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data="shop:open")])
    if query.message:
        await query.message.edit_text(
            _("shop-items-header", diamonds=user.diamonds),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
    await query.answer()


@router.callback_query(F.data == "shop:premium")
async def callback_shop_premium(query: CallbackQuery, user: User, _: Translator) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("btn-buy-premium-30d", price=payment_service.PREMIUM_PRICE_MONTHLY),
                    callback_data="buy:premium:30",
                )
            ],
            [InlineKeyboardButton(text=_("btn-back"), callback_data="shop:open")],
        ]
    )
    if query.message:
        await query.message.edit_text(_("shop-premium-info"), reply_markup=keyboard)
    await query.answer()


@router.callback_query(F.data.startswith("buy:item:"))
async def callback_buy_item(query: CallbackQuery, user: User, _: Translator) -> None:
    code = query.data.split(":")[2] if query.data else ""
    try:
        await payment_service.purchase_item(user, code, quantity=1)
    except payment_service.InsufficientDiamonds:
        await query.answer(_("buy-insufficient"), show_alert=True)
        return
    except ValueError:
        await query.answer("Invalid item", show_alert=True)
        return
    await query.answer(_("buy-success"), show_alert=False)


@router.callback_query(F.data.startswith("buy:premium:"))
async def callback_buy_premium(query: CallbackQuery, user: User, _: Translator) -> None:
    days_str = query.data.split(":")[2] if query.data else "30"
    try:
        days = int(days_str)
    except ValueError:
        days = 30
    try:
        await payment_service.buy_premium(user, days=days)
    except payment_service.InsufficientDiamonds:
        await query.answer(_("buy-insufficient"), show_alert=True)
        return
    await query.answer(_("premium-activated", days=days), show_alert=True)


@router.callback_query(F.data == "shop:close")
async def callback_shop_close(query: CallbackQuery, user: User, _: Translator) -> None:
    if query.message:
        await query.message.delete()
    await query.answer()
