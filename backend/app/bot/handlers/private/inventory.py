"""/profile (single-screen: profile + inventory + stats + shortcuts) + shop + exchange.

Mirrors @MafiaAzBot UX:
- One scrolling message with ID, name, balance, items, stats
- 5 inline toggles in 2 rows (fake_document, shield, mask | killer_shield, vote_shield)
- Shop / Buy buttons / Premium / News
- All callbacks use edit_message_text (no spam)
- Toggle states: 🟢 ON / 🔴 OFF / 🚫 0
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

from app.config import settings as app_settings
from app.db.models import User, UserInventory, UserStats
from app.services import exchange_service, payment_service, pricing_service
from app.services.i18n_service import Translator

router = Router(name="private_inventory")
router.message.filter(F.chat.type == "private")

# Display labels + emojis (used for both text + buttons)
ITEM_LABELS = {
    "shield": ("🛡", "Himoya"),
    "killer_shield": ("⛑", "Qotildan himoya"),
    "vote_shield": ("⚖️", "Ovoz himoyasi"),
    "rifle": ("🔫", "Miltiq"),
    "mask": ("🎭", "Maska"),
    "fake_document": ("📁", "Soxta hujjat"),
    "special_role": ("🃏", "Maxsus rol"),
}

# Toggleable items in profile menu (rifle/special_role are "use once" — not toggled here)
TOGGLE_ITEMS = ["fake_document", "shield", "mask", "killer_shield", "vote_shield"]


# === Build text + keyboard ===


async def _build_profile_message(
    user: User, inv: UserInventory, _: Translator
) -> tuple[str, InlineKeyboardMarkup]:
    """Single-screen profile (mirrors @MafiaAzBot)."""
    # Fetch stats
    stats = await UserStats.get_or_none(user_id=user.id)
    wins = stats.games_won if stats else 0
    games_total = stats.games_total if stats else 0

    # Next-game role display (special_role inventory tracks "next role queue")
    next_role_display = "—"
    inv_settings = inv.settings or {}
    next_role_pick = inv_settings.get("special_role", {}).get("next_role")
    if next_role_pick:
        emoji_role = _(f"role-{next_role_pick}")
        next_role_display = emoji_role or next_role_pick

    text = _(
        "profile-info",
        id=user.id,
        name=user.first_name,
        dollars=user.dollars,
        diamonds=user.diamonds,
        shield=getattr(inv, "shield", 0),
        killer_shield=getattr(inv, "killer_shield", 0),
        vote_shield=getattr(inv, "vote_shield", 0),
        rifle=getattr(inv, "rifle", 0),
        mask=getattr(inv, "mask", 0),
        fake_document=getattr(inv, "fake_document", 0),
        next_role=next_role_display,
        wins=wins,
        games_total=games_total,
    )

    # Build keyboard
    rows: list[list[InlineKeyboardButton]] = []

    # Row 1+2: toggleable items
    row1, row2 = [], []
    for i, code in enumerate(TOGGLE_ITEMS):
        emoji, _name = ITEM_LABELS[code]
        qty = getattr(inv, code, 0)
        enabled = inv_settings.get(code, {}).get("enabled", False)
        if qty <= 0:
            btn_text = _("btn-toggle-empty", emoji=emoji)
            cb = "inv:noop"
        elif enabled:
            btn_text = _("btn-toggle-on", emoji=emoji)
            cb = f"inv:toggle:{code}"
        else:
            btn_text = _("btn-toggle-off", emoji=emoji)
            cb = f"inv:toggle:{code}"
        btn = InlineKeyboardButton(text=btn_text, callback_data=cb)
        # First 3 in row 1, next 2 in row 2 (matches @MafiaAzBot layout)
        if i < 3:
            row1.append(btn)
        else:
            row2.append(btn)
    rows.append(row1)
    rows.append(row2)

    # Row 3: Shop
    rows.append([InlineKeyboardButton(text=_("btn-shop"), callback_data="shop:open")])

    # Row 4: Buy with dollars / Buy with diamonds (quick-shop shortcuts)
    rows.append(
        [
            InlineKeyboardButton(text=_("btn-buy-dollars"), callback_data="shop:items:dollars"),
            InlineKeyboardButton(text=_("btn-buy-diamonds"), callback_data="shop:items:diamonds"),
        ]
    )

    # Row "Pick next role" — visible only if user has a special_role
    # credit and hasn't picked their role for the next game yet.
    if getattr(inv, "special_role", 0) > 0 and not next_role_pick:
        rows.append(
            [InlineKeyboardButton(text=_("btn-pick-next-role"), callback_data="inv:pickrole")]
        )
    elif next_role_pick:
        rows.append(
            [InlineKeyboardButton(text=_("btn-clear-next-role"), callback_data="inv:clearrole")]
        )

    # Row 5: Premium
    rows.append([InlineKeyboardButton(text=_("btn-premium-groups"), callback_data="shop:premium")])

    # Row 6: News channel URL (external link)
    news_url = f"https://t.me/{app_settings.bot_username}_news"
    rows.append([InlineKeyboardButton(text=_("btn-news"), url=news_url)])

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


# === /profile (= /inventory = /items) ===


@router.message(Command("profile", "inventory", "items"))
async def cmd_profile(message: Message, user: User, _: Translator) -> None:
    """Single-screen profile: balance, inventory, stats, shortcuts.

    Mirrors @MafiaAzBot reference — all info in one message.
    """
    inv, _new = await UserInventory.get_or_create(user=user)
    text, kb = await _build_profile_message(user, inv, _)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


async def _refresh_profile(query: CallbackQuery, user: User, _: Translator) -> None:
    """Re-render profile in-place (edit message)."""
    refreshed = await User.get(id=user.id)
    user.diamonds = refreshed.diamonds
    user.dollars = refreshed.dollars
    inv, _new = await UserInventory.get_or_create(user=refreshed)
    text, kb = await _build_profile_message(refreshed, inv, _)
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# === Toggles ===


@router.callback_query(F.data == "inv:noop")
async def callback_inv_noop(query: CallbackQuery, _: Translator) -> None:
    """Clicked toggle on item with qty=0."""
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
    # UserInventory has OneToOneField(pk=True) — `inv.save()` breaks on
    # PostgreSQL. Use filter().update() with the explicit column kwarg.
    await UserInventory.filter(user_id=user.id).update(settings=settings)

    _emoji, name = ITEM_LABELS[code]
    state_text = _("inv-toggle-on") if new_state else _("inv-toggle-off")
    await query.answer(f"{name}: {state_text}", show_alert=False)
    await _refresh_profile(query, user, _)


@router.callback_query(F.data == "inv:close")
async def callback_inv_close(query: CallbackQuery, _: Translator) -> None:
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.delete()
    await query.answer()


@router.callback_query(F.data == "inv:back")
async def callback_inv_back(query: CallbackQuery, user: User, _: Translator) -> None:
    await _refresh_profile(query, user, _)
    await query.answer()


# === Next-game role picker (special_role item) ===


# Order mirrors the role catalog: 10 civilians, 5 mafia, 6 singletons.
_PICKABLE_ROLES: list[str] = [
    "citizen",
    "detective",
    "sergeant",
    "mayor",
    "doctor",
    "hooker",
    "hobo",
    "lucky",
    "suicide",
    "kamikaze",
    "don",
    "mafia",
    "lawyer",
    "journalist",
    "killer",
    "maniac",
    "werewolf",
    "mage",
    "arsonist",
    "crook",
    "snitch",
]


def _build_role_picker_kb(_: Translator) -> InlineKeyboardMarkup:
    """3-wide grid of all 21 roles + cancel row."""
    rows: list[list[InlineKeyboardButton]] = []
    bucket: list[InlineKeyboardButton] = []
    for code in _PICKABLE_ROLES:
        bucket.append(
            InlineKeyboardButton(text=_(f"role-{code}"), callback_data=f"inv:setrole:{code}")
        )
        if len(bucket) == 3:
            rows.append(bucket)
            bucket = []
    if bucket:
        rows.append(bucket)
    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data="inv:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "inv:pickrole")
async def callback_pick_role(query: CallbackQuery, user: User, _: Translator) -> None:
    """Show role grid for the special_role inventory item."""
    inv, _new = await UserInventory.get_or_create(user=user)
    if getattr(inv, "special_role", 0) <= 0:
        await query.answer(_("inv-no-items"), show_alert=True)
        return
    if (inv.settings or {}).get("special_role", {}).get("next_role"):
        await query.answer(_("pick-role-already-chosen"), show_alert=True)
        return
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(
                _("pick-role-prompt"),
                reply_markup=_build_role_picker_kb(_),
                parse_mode="HTML",
            )
    await query.answer()


@router.callback_query(F.data.startswith("inv:setrole:"))
async def callback_set_role(query: CallbackQuery, user: User, _: Translator) -> None:
    """Consume one special_role credit + save the picked role in settings."""
    if query.data is None:
        await query.answer()
        return
    role_code = query.data.split(":")[2]
    if role_code not in _PICKABLE_ROLES:
        await query.answer("Invalid role", show_alert=True)
        return

    inv, _new = await UserInventory.get_or_create(user=user)
    if getattr(inv, "special_role", 0) <= 0:
        await query.answer(_("inv-no-items"), show_alert=True)
        return

    settings = dict(inv.settings or {})
    sr = dict(settings.get("special_role", {}))
    if sr.get("next_role"):
        await query.answer(_("pick-role-already-chosen"), show_alert=True)
        return
    sr["next_role"] = role_code
    sr["enabled"] = True
    settings["special_role"] = sr
    new_count = inv.special_role - 1

    # OneToOneField(pk=True) → use filter().update() instead of .save().
    await UserInventory.filter(user_id=user.id).update(special_role=new_count, settings=settings)

    role_label = _(f"role-{role_code}")
    await query.answer(_("pick-role-confirmed", role=role_label), show_alert=True)
    await _refresh_profile(query, user, _)


@router.callback_query(F.data == "inv:clearrole")
async def callback_clear_role(query: CallbackQuery, user: User, _: Translator) -> None:
    """Drop the previously-chosen next role. (special_role credit is NOT
    refunded — picking is final once acted on.)"""
    inv, _new = await UserInventory.get_or_create(user=user)
    settings = dict(inv.settings or {})
    sr = dict(settings.get("special_role", {}))
    if not sr.get("next_role"):
        await query.answer()
        return
    sr.pop("next_role", None)
    sr["enabled"] = False
    settings["special_role"] = sr
    await UserInventory.filter(user_id=user.id).update(settings=settings)
    await query.answer(_("pick-role-cleared"), show_alert=False)
    await _refresh_profile(query, user, _)


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


def _matches_currency_filter(price_d: int, price_dia: int, want: str | None) -> bool:
    if want == "dollars":
        return price_d > 0
    if want == "diamonds":
        return price_dia > 0
    return price_d > 0 or price_dia > 0


@router.callback_query(F.data.startswith("shop:items"))
async def callback_shop_items(query: CallbackQuery, user: User, _: Translator) -> None:
    """callback_data: shop:items[:dollars|:diamonds] — filter items list."""
    parts = (query.data or "").split(":")
    cur_filter = parts[2] if len(parts) >= 3 else None  # None = both

    rows = []
    for spec in payment_service.ITEM_CATALOG:
        emoji, name = ITEM_LABELS.get(spec.code, ("", spec.code))
        label = f"{emoji} {name}"
        dollars, diamonds = await pricing_service.get_item_price(spec.code)
        if not _matches_currency_filter(dollars, diamonds, cur_filter):
            continue

        # Decide which currency to use when both available
        if cur_filter == "dollars" and dollars > 0:
            price_label = f"💵 {dollars}"
            cb = f"buy:item:{spec.code}:dollars"
        elif (cur_filter == "diamonds" and diamonds > 0) or diamonds > 0:
            price_label = f"💎 {diamonds}"
            cb = f"buy:item:{spec.code}:diamonds"
        elif dollars > 0:
            price_label = f"💵 {dollars}"
            cb = f"buy:item:{spec.code}:dollars"
        else:
            continue
        rows.append([InlineKeyboardButton(text=f"{label} — {price_label}", callback_data=cb)])

    if not rows:
        rows.append([InlineKeyboardButton(text=_("shop-no-items"), callback_data="inv:back")])

    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data="inv:back")])
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
            [InlineKeyboardButton(text=_("btn-back"), callback_data="inv:back")],
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

    emoji, name = ITEM_LABELS.get(spec.code, ("", spec.code))
    label = f"{emoji} {name}"
    cur_emoji = "💎" if used_currency == "diamonds" else "💵"
    await query.answer(
        _("buy-success-detailed", item=label, cost=cost, currency=cur_emoji),
        show_alert=True,
    )
    await _refresh_profile(query, user, _)


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
    await _refresh_profile(query, user, _)


# === Exchange ===


def _build_exchange_kb(rate: int, _: Translator) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
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


@router.message(Command("exchange"))
async def cmd_exchange(message: Message, user: User, _: Translator) -> None:
    rate = await pricing_service.get_diamond_to_dollar_rate()
    text = _("exchange-menu", diamonds=user.diamonds, dollars=user.dollars, rate=rate)
    await message.answer(text, reply_markup=_build_exchange_kb(rate, _), parse_mode="HTML")


@router.callback_query(F.data == "exchange:open")
async def callback_exchange_open(query: CallbackQuery, user: User, _: Translator) -> None:
    rate = await pricing_service.get_diamond_to_dollar_rate()
    text = _("exchange-menu", diamonds=user.diamonds, dollars=user.dollars, rate=rate)
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(
                text, reply_markup=_build_exchange_kb(rate, _), parse_mode="HTML"
            )
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
    await callback_exchange_open(query, user, _)


logger.info("Inventory + shop + exchange handlers loaded")
