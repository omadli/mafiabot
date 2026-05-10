"""/profile, /inventory, /buy, /exchange — private chat.

Uses callback_query.message.edit_text (not new messages) for clean UX.
Toggle buttons use ✅/❌ (not ⬜) to be explicit about state.
"""

from __future__ import annotations

import contextlib

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from loguru import logger

from app.db.models import User, UserInventory
from app.services import exchange_service, payment_service, pricing_service
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


# === /profile ===


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


# === /inventory ===


def _build_inventory_text_and_kb(
    inv: UserInventory, _: Translator
) -> tuple[str, InlineKeyboardMarkup]:
    """Build inventory message text + keyboard (used for both initial /inventory and refresh)."""
    settings = inv.settings or {}
    lines = [_("inventory-header")]
    keyboard_rows: list[list[InlineKeyboardButton]] = []

    for code, label in ITEM_LABELS.items():
        qty = getattr(inv, code, 0)
        item_settings = settings.get(code, {})
        enabled = item_settings.get("enabled", False)
        toggle = "✅" if enabled else "❌"

        # Disable toggling if no items owned (qty == 0)
        if qty <= 0:
            toggle = "🚫"  # cannot toggle without owning
            btn_text = f"{toggle} {label} (0)"
            cb = "inv:noop"
        else:
            btn_text = f"{toggle} {label} ({qty})"
            cb = f"inv:toggle:{code}"

        lines.append(f"  {toggle} {label}: <b>{qty}</b>")
        keyboard_rows.append([InlineKeyboardButton(text=btn_text, callback_data=cb)])

    keyboard_rows.append(
        [
            InlineKeyboardButton(text=_("btn-shop"), callback_data="shop:open"),
            InlineKeyboardButton(text=_("btn-exchange"), callback_data="exchange:open"),
        ]
    )
    keyboard_rows.append([InlineKeyboardButton(text=_("btn-close"), callback_data="inv:close")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


@router.message(Command("inventory", "items"))
async def cmd_inventory(message: Message, user: User, _: Translator) -> None:
    """Show inventory."""
    inv, _new = await UserInventory.get_or_create(user=user)
    text, kb = _build_inventory_text_and_kb(inv, _)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


async def _refresh_inventory(query: CallbackQuery, user: User, _: Translator) -> None:
    """Re-render inventory in-place (edit message)."""
    inv, _new = await UserInventory.get_or_create(user=user)
    text, kb = _build_inventory_text_and_kb(inv, _)
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "inv:noop")
async def callback_inv_noop(query: CallbackQuery, _: Translator) -> None:
    """Clicked toggle on item with qty=0 — explain user has none."""
    await query.answer(_("inv-no-items"), show_alert=False)


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
    qty = getattr(inv, code, 0)
    if qty <= 0:
        await query.answer(_("inv-no-items"), show_alert=False)
        return

    settings = dict(inv.settings or {})
    item_s = dict(settings.get(code, {"enabled": False}))
    new_state = not item_s.get("enabled", False)
    item_s["enabled"] = new_state
    settings[code] = item_s
    inv.settings = settings
    await inv.save(update_fields=["settings"])

    state_text = _("inv-toggle-on") if new_state else _("inv-toggle-off")
    await query.answer(f"{ITEM_LABELS[code]}: {state_text}", show_alert=False)
    await _refresh_inventory(query, user, _)


@router.callback_query(F.data == "inv:close")
async def callback_inv_close(query: CallbackQuery, _: Translator) -> None:
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.delete()
    await query.answer()


@router.callback_query(F.data == "inv:back")
async def callback_inv_back(query: CallbackQuery, user: User, _: Translator) -> None:
    await _refresh_inventory(query, user, _)
    await query.answer()


# === Shop ===


@router.callback_query(F.data == "shop:open")
async def callback_shop(query: CallbackQuery, user: User, _: Translator) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("btn-buy-diamonds"), callback_data="shop:diamonds")],
            [InlineKeyboardButton(text=_("btn-buy-items"), callback_data="shop:items")],
            [InlineKeyboardButton(text=_("btn-buy-premium"), callback_data="shop:premium")],
            [InlineKeyboardButton(text=_("btn-back"), callback_data="inv:back")],
        ]
    )
    if query.message:
        text = _(
            "shop-welcome-balance",
            diamonds=user.diamonds,
            dollars=user.dollars,
        )
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
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
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(
                _("shop-diamonds-header"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                parse_mode="HTML",
            )
    await query.answer()


@router.callback_query(F.data == "shop:items")
async def callback_shop_items(query: CallbackQuery, user: User, _: Translator) -> None:
    rows = []
    for spec in payment_service.ITEM_CATALOG:
        label = ITEM_LABELS.get(spec.code, spec.code)
        dollars, diamonds = await pricing_service.get_item_price(spec.code)
        if diamonds > 0:
            price_label = f"💎 {diamonds}"
            cb = f"buy:item:{spec.code}:diamonds"
        elif dollars > 0:
            price_label = f"💵 {dollars}"
            cb = f"buy:item:{spec.code}:dollars"
        else:
            continue  # disabled item
        rows.append([InlineKeyboardButton(text=f"{label} — {price_label}", callback_data=cb)])

    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data="shop:open")])
    if query.message:
        text = _("shop-items-header", diamonds=user.diamonds, dollars=user.dollars)
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                parse_mode="HTML",
            )
    await query.answer()


@router.callback_query(F.data == "shop:premium")
async def callback_shop_premium(query: CallbackQuery, user: User, _: Translator) -> None:
    monthly_price = await pricing_service.get_premium_price(30)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("btn-buy-premium-30d", price=monthly_price),
                    callback_data="buy:premium:30",
                )
            ],
            [InlineKeyboardButton(text=_("btn-back"), callback_data="shop:open")],
        ]
    )
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(
                _("shop-premium-info"), reply_markup=keyboard, parse_mode="HTML"
            )
    await query.answer()


@router.callback_query(F.data.startswith("buy:item:"))
async def callback_buy_item(query: CallbackQuery, user: User, _: Translator) -> None:
    """callback_data: buy:item:<code>:<currency>"""
    parts = (query.data or "").split(":")
    if len(parts) < 3:
        await query.answer("Invalid", show_alert=True)
        return
    code = parts[2]
    currency = parts[3] if len(parts) >= 4 else None
    try:
        spec, used_currency, cost = await payment_service.purchase_item(
            user, code, quantity=1, currency=currency
        )
    except payment_service.InsufficientDiamonds:
        await query.answer(_("buy-insufficient-diamonds"), show_alert=True)
        return
    except payment_service.InsufficientDollars:
        await query.answer(_("buy-insufficient-dollars"), show_alert=True)
        return
    except ValueError:
        await query.answer("Invalid item", show_alert=True)
        return

    label = ITEM_LABELS.get(spec.code, spec.code)
    cur_emoji = "💎" if used_currency == "diamonds" else "💵"
    await query.answer(
        _("buy-success-detailed", item=label, cost=cost, currency=cur_emoji),
        show_alert=True,
    )

    # Refresh user balance & re-render shop:items
    refreshed = await User.get(id=user.id)
    user.diamonds = refreshed.diamonds
    user.dollars = refreshed.dollars
    await callback_shop_items(query, user, _)


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
        await query.answer(_("buy-insufficient-diamonds"), show_alert=True)
        return
    await query.answer(_("premium-activated", days=days), show_alert=True)


@router.callback_query(F.data == "shop:close")
async def callback_shop_close(query: CallbackQuery, user: User, _: Translator) -> None:
    await callback_inv_back(query, user, _)


# === Exchange (diamonds ↔ dollars) ===


@router.message(Command("exchange"))
async def cmd_exchange(message: Message, user: User, _: Translator) -> None:
    rate = await pricing_service.get_diamond_to_dollar_rate()
    text = _(
        "exchange-menu",
        diamonds=user.diamonds,
        dollars=user.dollars,
        rate=rate,
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 → 💵", callback_data="exchange:d2d:1"),
                InlineKeyboardButton(text="💎×5 → 💵", callback_data="exchange:d2d:5"),
                InlineKeyboardButton(text="💎×10 → 💵", callback_data="exchange:d2d:10"),
            ],
            [
                InlineKeyboardButton(text=f"💵{rate} → 💎", callback_data=f"exchange:r2d:{rate}"),
                InlineKeyboardButton(
                    text=f"💵{rate * 5} → 💎×5", callback_data=f"exchange:r2d:{rate * 5}"
                ),
            ],
            [InlineKeyboardButton(text=_("btn-close"), callback_data="inv:close")],
        ]
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "exchange:open")
async def callback_exchange_open(query: CallbackQuery, user: User, _: Translator) -> None:
    rate = await pricing_service.get_diamond_to_dollar_rate()
    text = _(
        "exchange-menu",
        diamonds=user.diamonds,
        dollars=user.dollars,
        rate=rate,
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 → 💵", callback_data="exchange:d2d:1"),
                InlineKeyboardButton(text="💎×5 → 💵", callback_data="exchange:d2d:5"),
                InlineKeyboardButton(text="💎×10 → 💵", callback_data="exchange:d2d:10"),
            ],
            [
                InlineKeyboardButton(text=f"💵{rate} → 💎", callback_data=f"exchange:r2d:{rate}"),
                InlineKeyboardButton(
                    text=f"💵{rate * 5} → 💎×5", callback_data=f"exchange:r2d:{rate * 5}"
                ),
            ],
            [InlineKeyboardButton(text=_("btn-back"), callback_data="inv:back")],
        ]
    )
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()


@router.callback_query(F.data.startswith("exchange:d2d:"))
async def callback_exchange_d2d(query: CallbackQuery, user: User, _: Translator) -> None:
    """Diamonds → Dollars."""
    try:
        amount = int((query.data or "").split(":")[2])
    except (ValueError, IndexError):
        await query.answer("Invalid", show_alert=True)
        return
    try:
        dollars = await exchange_service.diamonds_to_dollars(user, amount)
    except exchange_service.ExchangeDisabled:
        await query.answer(_("exchange-disabled"), show_alert=True)
        return
    except exchange_service.InsufficientBalance:
        await query.answer(_("exchange-insufficient-diamonds"), show_alert=True)
        return
    except exchange_service.BelowMinimum:
        await query.answer(_("exchange-below-minimum"), show_alert=True)
        return

    await query.answer(_("exchange-success", got=dollars, currency="💵"), show_alert=True)
    refreshed = await User.get(id=user.id)
    user.diamonds = refreshed.diamonds
    user.dollars = refreshed.dollars
    await callback_exchange_open(query, user, _)


@router.callback_query(F.data.startswith("exchange:r2d:"))
async def callback_exchange_r2d(query: CallbackQuery, user: User, _: Translator) -> None:
    """Dollars → Diamonds."""
    try:
        amount = int((query.data or "").split(":")[2])
    except (ValueError, IndexError):
        await query.answer("Invalid", show_alert=True)
        return
    try:
        diamonds = await exchange_service.dollars_to_diamonds(user, amount)
    except exchange_service.ExchangeDisabled:
        await query.answer(_("exchange-disabled"), show_alert=True)
        return
    except exchange_service.InsufficientBalance:
        await query.answer(_("exchange-insufficient-dollars"), show_alert=True)
        return
    except exchange_service.BelowMinimum:
        await query.answer(_("exchange-below-minimum"), show_alert=True)
        return

    await query.answer(_("exchange-success", got=diamonds, currency="💎"), show_alert=True)
    refreshed = await User.get(id=user.id)
    user.diamonds = refreshed.diamonds
    user.dollars = refreshed.dollars
    await callback_exchange_open(query, user, _)


logger.info("Inventory + shop + exchange handlers loaded")
