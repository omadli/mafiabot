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
from datetime import UTC, datetime

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

from app.db.models import User, UserInventory, UserStats
from app.services import exchange_service, payment_service, pricing_service
from app.services.i18n_service import Translator


def _premium_status(user: User) -> tuple[bool, datetime | None]:
    """Return (is_active, expires_at). Both flag AND expiry must check
    out — a stale `is_premium=True` after the expiry date is treated as
    inactive (the cron that resets the flag may not have run yet).
    """
    expires_at = user.premium_expires_at
    if user.is_premium and expires_at is not None and expires_at > datetime.now(UTC):
        return True, expires_at
    return False, expires_at


def _format_premium_date(expires_at: datetime | None) -> str:
    """Render the expiry as `dd.mm.yyyy` — the format the operator's
    region expects on receipts and screenshots. Time component is
    dropped intentionally (premium tiers count in whole days) so the
    string fits the inventory header alongside the 👑 chip without
    line-wrapping on Telegram's mobile layout."""
    if expires_at is None:
        return "—"
    return expires_at.strftime("%d.%m.%Y")


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

# Item order shown in the shop (matches @MafiaAzBot reference). Distinct
# from ITEM_LABELS dict order so reorders here don't require touching the
# inventory display ordering.
SHOP_ITEM_ORDER = [
    "shield",
    "fake_document",
    "rifle",
    "vote_shield",
    "mask",
    "killer_shield",
    "special_role",
]


# === Build text + keyboard ===


async def _build_profile_message(
    user: User, inv: UserInventory, _: Translator, _plain: Translator
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

    # Premium status line — shown beneath the balance. Active premium
    # displays the expiry date; otherwise "not purchased". Trailing
    # whitespace is intentionally absent so the template doesn't render
    # an extra blank line when the line is short.
    is_active, expires_at = _premium_status(user)
    if is_active:
        premium_line = _("profile-premium-active", expires_at=_format_premium_date(expires_at))
    else:
        premium_line = _("profile-premium-inactive")

    text = _(
        "profile-info",
        # Pass as str so Fluent doesn't apply locale digit grouping
        # (e.g., "1 234 567 890") to the Telegram user ID.
        id=str(user.id),
        name=user.first_name,
        dollars=user.dollars,
        diamonds=user.diamonds,
        premium_line=premium_line,
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

    # Row 3: Do'kon | Premium — shop opens items menu directly,
    # premium opens duration picker (30/365 days).
    rows.append(
        [
            InlineKeyboardButton(text=_plain("btn-shop"), callback_data="shop:items"),
            InlineKeyboardButton(text=_plain("btn-buy-premium"), callback_data="shop:premium"),
        ]
    )

    # Row 4: 💵 Xarid qilish (diamonds → dollars) | 💎 Olmos sotib olish (Stars)
    rows.append(
        [
            InlineKeyboardButton(text=_plain("btn-buy-dollars"), callback_data="exchange:open"),
            InlineKeyboardButton(text=_plain("btn-buy-diamonds"), callback_data="shop:diamonds"),
        ]
    )

    # Row 5: Premium guruhlar (top ads list)
    rows.append(
        [
            InlineKeyboardButton(
                text=_plain("btn-premium-groups"), callback_data="premiumgroups:open"
            )
        ]
    )

    # Row 6: official news channel (separate handle, NOT derived from bot_username)
    rows.append([InlineKeyboardButton(text=_plain("btn-news"), url="https://t.me/Mafiauzbot_news")])

    # Clear-next-role row remains conditional — only when user has queued a role.
    if next_role_pick:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_plain("btn-clear-next-role"), callback_data="inv:clearrole"
                )
            ]
        )

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


# === /profile (= /inventory = /items) ===


@router.message(Command("profile", "inventory", "items"))
async def cmd_profile(
    message: Message, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Single-screen profile: balance, inventory, stats, shortcuts.

    Mirrors @MafiaAzBot reference — all info in one message.
    """
    inv, _new = await UserInventory.get_or_create(user=user)
    text, kb = await _build_profile_message(user, inv, _, _plain)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


async def _refresh_profile(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Re-render profile in-place (edit message)."""
    refreshed = await User.get(id=user.id)
    user.diamonds = refreshed.diamonds
    user.dollars = refreshed.dollars
    inv, _new = await UserInventory.get_or_create(user=refreshed)
    text, kb = await _build_profile_message(refreshed, inv, _, _plain)
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")  # type: ignore[union-attr]


# === Toggles ===


@router.callback_query(F.data == "inv:noop")
async def callback_inv_noop(
    query: CallbackQuery, _: Translator, _plain: Translator | None = None
) -> None:
    """Clicked toggle on item with qty=0."""
    await query.answer(_plain("inv-no-items"), show_alert=False)


@router.callback_query(F.data.startswith("inv:toggle:"))
async def callback_toggle_item(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
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
        await query.answer(_plain("inv-no-items"), show_alert=False)
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

    # If the user is mid-game, push the change into the live Redis state
    # immediately — otherwise the toggle is only honored on the next game.
    try:
        from app.services.game_service import sync_inventory_into_active_game

        await sync_inventory_into_active_game(user.id, code)
    except Exception as e:
        logger.debug(f"live-toggle sync failed for user {user.id}/{code}: {e}")

    _emoji, name = ITEM_LABELS[code]
    state_text = _("inv-toggle-on") if new_state else _("inv-toggle-off")
    await query.answer(f"{name}: {state_text}", show_alert=False)
    await _refresh_profile(query, user, _, _plain)


@router.callback_query(F.data == "inv:close")
async def callback_inv_close(
    query: CallbackQuery, _: Translator, _plain: Translator | None = None
) -> None:
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.delete()  # type: ignore[union-attr]
    await query.answer()


@router.callback_query(F.data == "inv:back")
async def callback_inv_back(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    await _refresh_profile(query, user, _, _plain)
    await query.answer()


# === Next-game role picker (special_role item) ===


# Order mirrors the role catalog: 9 civilians, 5 mafia, 7 singletons.
# Suidsid is a singleton (solo win: voted out wins, killed at night loses).
_PICKABLE_ROLES: list[str] = [
    "citizen",
    "detective",
    "sergeant",
    "mayor",
    "doctor",
    "hooker",
    "hobo",
    "lucky",
    "kamikaze",
    "don",
    "mafia",
    "lawyer",
    "journalist",
    "killer",
    "suicide",
    "maniac",
    "werewolf",
    "mage",
    "arsonist",
    "crook",
    "snitch",
]


def _build_role_picker_kb(_: Translator, _plain: Translator | None = None) -> InlineKeyboardMarkup:
    """3-wide grid of all 21 roles + cancel row."""
    rows: list[list[InlineKeyboardButton]] = []
    bucket: list[InlineKeyboardButton] = []
    for code in _PICKABLE_ROLES:
        bucket.append(
            InlineKeyboardButton(text=_plain(f"role-{code}"), callback_data=f"inv:setrole:{code}")
        )
        if len(bucket) == 3:
            rows.append(bucket)
            bucket = []
    if bucket:
        rows.append(bucket)
    rows.append([InlineKeyboardButton(text=_plain("btn-back"), callback_data="inv:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "inv:pickrole")
async def callback_pick_role(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Show role grid for the special_role inventory item."""
    inv, _new = await UserInventory.get_or_create(user=user)
    if getattr(inv, "special_role", 0) <= 0:
        await query.answer(_plain("inv-no-items"), show_alert=True)
        return
    if (inv.settings or {}).get("special_role", {}).get("next_role"):
        await query.answer(_plain("pick-role-already-chosen"), show_alert=True)
        return
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(  # type: ignore[union-attr]
                _("pick-role-prompt"),
                reply_markup=_build_role_picker_kb(_, _plain),
                parse_mode="HTML",
            )
    await query.answer()


@router.callback_query(F.data.startswith("inv:setrole:"))
async def callback_set_role(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
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
        await query.answer(_plain("inv-no-items"), show_alert=True)
        return

    settings = dict(inv.settings or {})
    sr = dict(settings.get("special_role", {}))
    if sr.get("next_role"):
        await query.answer(_plain("pick-role-already-chosen"), show_alert=True)
        return
    sr["next_role"] = role_code
    sr["enabled"] = True
    settings["special_role"] = sr
    new_count = inv.special_role - 1

    # OneToOneField(pk=True) → use filter().update() instead of .save().
    await UserInventory.filter(user_id=user.id).update(special_role=new_count, settings=settings)

    role_label = _(f"role-{role_code}")
    await query.answer(_plain("pick-role-confirmed", role=role_label), show_alert=True)
    await _refresh_profile(query, user, _, _plain)


@router.callback_query(F.data == "inv:clearrole")
async def callback_clear_role(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
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
    await query.answer(_plain("pick-role-cleared"), show_alert=False)
    await _refresh_profile(query, user, _, _plain)


# === Shop ===


@router.callback_query(F.data == "shop:diamonds")
async def callback_shop_diamonds(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    # Load the live package list — SystemSettings.diamond_packages
    # overrides the hard-coded defaults when SA has tweaked them.
    packages = await payment_service.list_diamond_packages()
    rows = []
    for pkg in packages:
        # Display the BASE diamonds + optional bonus separately so the
        # arithmetic is clear: "💎 150 🎁+15 — ⭐ 125" reads as
        # 150 base + 15 bonus = 165 total at 125 stars. The previous
        # "{base+bonus} 🎁+{bonus}" form misled buyers into thinking
        # the bonus was added on top of an already-bonused amount.
        bonus_label = f" 🎁+{pkg.bonus_diamonds}" if pkg.bonus_diamonds else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💎 {pkg.diamonds}{bonus_label} — ⭐ {pkg.stars_price}",
                    callback_data=f"buy:diamonds:{pkg.code}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=_plain("btn-back"), callback_data="inv:back")])
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(  # type: ignore[union-attr]
                _("shop-diamonds-header"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                parse_mode="HTML",
            )
    await query.answer()


async def _render_shop_items(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Render the items shop in-place. Refreshes balance from DB."""
    refreshed = await User.get(id=user.id)
    user.diamonds = refreshed.diamonds
    user.dollars = refreshed.dollars

    rows: list[list[InlineKeyboardButton]] = []
    for code in SHOP_ITEM_ORDER:
        spec = payment_service.get_item(code)
        if spec is None:
            continue
        emoji, name = ITEM_LABELS.get(code, ("", code))
        label = f"{emoji} {name}"
        dollars, diamonds = await pricing_service.get_item_price(code)

        if code == "special_role":
            # Special role: pick the role first, pay on confirm.
            price_label = f"💎 {diamonds}" if diamonds > 0 else f"💵 {dollars}"
            cb = "shop:special:pick"
        elif diamonds > 0:
            price_label = f"💎 {diamonds}"
            cb = f"buy:item:{code}:diamonds"
        elif dollars > 0:
            price_label = f"💵 {dollars}"
            cb = f"buy:item:{code}:dollars"
        else:
            continue
        rows.append([InlineKeyboardButton(text=f"{label} — {price_label}", callback_data=cb)])

    if not rows:
        rows.append([InlineKeyboardButton(text=_plain("shop-no-items"), callback_data="inv:back")])

    rows.append([InlineKeyboardButton(text=_plain("btn-back"), callback_data="inv:back")])
    if query.message:
        text = _("shop-items-header", diamonds=refreshed.diamonds, dollars=refreshed.dollars)
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(  # type: ignore[union-attr]
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                parse_mode="HTML",
            )


@router.callback_query(F.data == "shop:items")
async def callback_shop_items(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Items shop — fixed display order, special_role opens a role picker."""
    await _render_shop_items(query, user, _, _plain)
    await query.answer()


# === Special-role purchase flow (pick + buy in one step) ===


@router.callback_query(F.data == "shop:special:pick")
async def callback_shop_special_pick(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Show the 21-role grid; clicking a role triggers purchase + queue."""
    inv, _new = await UserInventory.get_or_create(user=user)
    if (inv.settings or {}).get("special_role", {}).get("next_role"):
        await query.answer(_plain("pick-role-already-chosen"), show_alert=True)
        return

    dollars, diamonds = await pricing_service.get_item_price("special_role")
    price_label = f"💎 {diamonds}" if diamonds > 0 else f"💵 {dollars}"

    rows: list[list[InlineKeyboardButton]] = []
    bucket: list[InlineKeyboardButton] = []
    for code in _PICKABLE_ROLES:
        bucket.append(
            InlineKeyboardButton(
                text=_plain(f"role-{code}"), callback_data=f"shop:special:buy:{code}"
            )
        )
        if len(bucket) == 3:
            rows.append(bucket)
            bucket = []
    if bucket:
        rows.append(bucket)
    rows.append([InlineKeyboardButton(text=_plain("btn-back"), callback_data="shop:items")])

    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(  # type: ignore[union-attr]
                _("shop-special-pick-prompt", price=price_label),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                parse_mode="HTML",
            )
    await query.answer()


@router.callback_query(F.data.startswith("shop:special:buy:"))
async def callback_shop_special_buy(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Pay for special_role and immediately queue the chosen role."""
    if query.data is None:
        await query.answer()
        return
    role_code = query.data.split(":")[3]
    if role_code not in _PICKABLE_ROLES:
        await query.answer("Invalid role", show_alert=True)
        return

    inv, _new = await UserInventory.get_or_create(user=user)
    if (inv.settings or {}).get("special_role", {}).get("next_role"):
        await query.answer(_plain("pick-role-already-chosen"), show_alert=True)
        return

    try:
        _spec, used_currency, cost = await payment_service.purchase_item(
            user, "special_role", quantity=1
        )
    except payment_service.InsufficientDiamonds:
        await query.answer(_plain("buy-insufficient-diamonds"), show_alert=True)
        return
    except payment_service.InsufficientDollars:
        await query.answer(_plain("buy-insufficient-dollars"), show_alert=True)
        return

    # Queue the chosen role now that the credit is in the inventory.
    refreshed = await UserInventory.get(user_id=user.id)
    settings = dict(refreshed.settings or {})
    sr = dict(settings.get("special_role", {}))
    sr["next_role"] = role_code
    sr["enabled"] = True
    settings["special_role"] = sr
    await UserInventory.filter(user_id=user.id).update(settings=settings)

    cur_emoji = "💎" if used_currency == "diamonds" else "💵"
    role_label = _plain(f"role-{role_code}")
    await query.answer(
        _plain("shop-special-purchased", role=role_label, cost=cost, currency=cur_emoji),
        show_alert=True,
    )
    await _refresh_profile(query, user, _, _plain)


@router.callback_query(F.data == "shop:premium")
async def callback_shop_premium(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Premium purchase screen.

    Switches to "extend" mode when the caller already has an active
    premium subscription — header shows the current expiry date and the
    buttons read "extend by 30 days / 1 year" instead of "buy".
    Prices are identical in both modes (extend == add to current expiry).
    """
    # Re-read user so the active flag/expiry are fresh even if the cached
    # `user` arg lagged behind a recent purchase.
    refreshed = await User.get(id=user.id)
    is_active, expires_at = _premium_status(refreshed)

    monthly_price = await pricing_service.get_premium_price(30)
    yearly_price = await pricing_service.get_premium_price(365)

    if is_active:
        header_text = _(
            "shop-premium-info-active",
            expires_at=_format_premium_date(expires_at),
        )
        btn_30 = _plain("btn-extend-premium-30d", price=monthly_price)
        btn_365 = _plain("btn-extend-premium-365d", price=yearly_price)
    else:
        header_text = _("shop-premium-info")
        btn_30 = _plain("btn-buy-premium-30d", price=monthly_price)
        btn_365 = _plain("btn-buy-premium-365d", price=yearly_price)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_30, callback_data="buy:premium:30")],
            [InlineKeyboardButton(text=btn_365, callback_data="buy:premium:365")],
            [InlineKeyboardButton(text=_plain("btn-back"), callback_data="inv:back")],
        ]
    )
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(  # type: ignore[union-attr]
                header_text, reply_markup=keyboard, parse_mode="HTML"
            )
    await query.answer()


@router.callback_query(F.data.startswith("buy:item:"))
async def callback_buy_item(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
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
        await query.answer(_plain("buy-insufficient-diamonds"), show_alert=True)
        return
    except payment_service.InsufficientDollars:
        await query.answer(_plain("buy-insufficient-dollars"), show_alert=True)
        return
    except ValueError:
        await query.answer("Invalid item", show_alert=True)
        return

    # Auto-enable toggleable items right after purchase — saves the user
    # the extra tap on the profile page. Rifle/special_role are not in
    # TOGGLE_ITEMS so they are unaffected here.
    if spec.code in TOGGLE_ITEMS:
        inv = await UserInventory.get(user_id=user.id)
        inv_settings = dict(inv.settings or {})
        item_s = dict(inv_settings.get(spec.code, {}))
        item_s["enabled"] = True
        inv_settings[spec.code] = item_s
        await UserInventory.filter(user_id=user.id).update(settings=inv_settings)

        # Live-game sync — same path as toggle. If the buyer is alive
        # in an active game, the freshly-bought-and-enabled item is
        # consumed and added to their in-game items_active right away.
        try:
            from app.services.game_service import sync_inventory_into_active_game

            await sync_inventory_into_active_game(user.id, spec.code)
        except Exception as e:
            logger.debug(f"live-buy sync failed for user {user.id}/{spec.code}: {e}")

    emoji, name = ITEM_LABELS.get(spec.code, ("", spec.code))
    label = f"{emoji} {name}"
    cur_emoji = "💎" if used_currency == "diamonds" else "💵"
    await query.answer(
        _plain("buy-success-detailed", item=label, cost=cost, currency=cur_emoji),
        show_alert=True,
    )
    # Stay on the shop screen instead of jumping back to the profile —
    # the user almost always wants to buy more than one item per visit.
    await _render_shop_items(query, user, _, _plain)


@router.callback_query(F.data.startswith("buy:premium:"))
async def callback_buy_premium(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    days_str = query.data.split(":")[2] if query.data else "30"
    try:
        days = int(days_str)
    except ValueError:
        days = 30

    # Snapshot active-state BEFORE the purchase — we need it to pick the
    # right alert template (activate vs extend).
    was_active, _prev_expires = _premium_status(user)

    try:
        await payment_service.buy_premium(user, days=days)
    except payment_service.InsufficientDiamonds:
        await query.answer(_plain("buy-insufficient-diamonds"), show_alert=True)
        return

    # Re-read the user so the alert quotes the actual new expiry date
    # (buy_premium adds to existing expiry, not to "now").
    refreshed = await User.get(id=user.id)
    _is_active, new_expires = _premium_status(refreshed)
    expires_label = _format_premium_date(new_expires)
    key = "premium-extended" if was_active else "premium-activated"
    await query.answer(
        _plain(key, days=days, expires_at=expires_label),
        show_alert=True,
    )
    await _refresh_profile(query, user, _, _plain)


# === Exchange ===


def _build_exchange_kb(
    rate: int, _: Translator, _plain: Translator | None = None
) -> InlineKeyboardMarkup:
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
            [InlineKeyboardButton(text=_plain("btn-back"), callback_data="inv:back")],
        ]
    )


@router.message(Command("exchange"))
async def cmd_exchange(
    message: Message, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    rate = await pricing_service.get_diamond_to_dollar_rate()
    text = _("exchange-menu", diamonds=user.diamonds, dollars=user.dollars, rate=rate)
    await message.answer(text, reply_markup=_build_exchange_kb(rate, _, _plain), parse_mode="HTML")


async def _render_exchange_menu(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Re-render exchange menu in-place, refreshing balance from DB."""
    refreshed = await User.get(id=user.id)
    user.diamonds = refreshed.diamonds
    user.dollars = refreshed.dollars
    rate = await pricing_service.get_diamond_to_dollar_rate()
    text = _("exchange-menu", diamonds=refreshed.diamonds, dollars=refreshed.dollars, rate=rate)
    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(  # type: ignore[union-attr]
                text, reply_markup=_build_exchange_kb(rate, _, _plain), parse_mode="HTML"
            )


@router.callback_query(F.data == "exchange:open")
async def callback_exchange_open(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    await _render_exchange_menu(query, user, _, _plain)
    await query.answer()


@router.callback_query(F.data.startswith("exchange:d2d:"))
async def callback_exchange_d2d(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Diamonds → Dollars."""
    try:
        amount = int((query.data or "").split(":")[2])
    except (ValueError, IndexError):
        await query.answer("Invalid", show_alert=True)
        return
    try:
        dollars = await exchange_service.diamonds_to_dollars(user, amount)
    except exchange_service.ExchangeDisabled:
        await query.answer(_plain("exchange-disabled"), show_alert=True)
        return
    except exchange_service.InsufficientBalance:
        await query.answer(_plain("exchange-insufficient-diamonds"), show_alert=True)
        return
    except exchange_service.BelowMinimum:
        await query.answer(_plain("exchange-below-minimum"), show_alert=True)
        return

    await query.answer(_plain("exchange-success", got=dollars, currency="💵"), show_alert=True)
    await _render_exchange_menu(query, user, _, _plain)


@router.callback_query(F.data.startswith("exchange:r2d:"))
async def callback_exchange_r2d(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Dollars → Diamonds."""
    try:
        amount = int((query.data or "").split(":")[2])
    except (ValueError, IndexError):
        await query.answer("Invalid", show_alert=True)
        return
    try:
        diamonds = await exchange_service.dollars_to_diamonds(user, amount)
    except exchange_service.ExchangeDisabled:
        await query.answer(_plain("exchange-disabled"), show_alert=True)
        return
    except exchange_service.InsufficientBalance:
        await query.answer(_plain("exchange-insufficient-dollars"), show_alert=True)
        return
    except exchange_service.BelowMinimum:
        await query.answer(_plain("exchange-below-minimum"), show_alert=True)
        return

    await query.answer(_plain("exchange-success", got=diamonds, currency="💎"), show_alert=True)
    await _render_exchange_menu(query, user, _, _plain)


# === Premium groups (ads / top list) ===


@router.callback_query(F.data == "premiumgroups:open")
async def callback_premium_groups(
    query: CallbackQuery, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Show top premium groups by total games. Each row links to invite URL if set."""
    top = await pricing_service.get_premium_groups_top(limit=10)

    if not top:
        text = _("premium-groups-empty")
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=_plain("btn-back"), callback_data="inv:back")],
            ]
        )
    else:
        multiplier = await pricing_service.get_group_reward_multiplier()
        lines = [_("premium-groups-header", multiplier=multiplier), ""]
        rows: list[list[InlineKeyboardButton]] = []
        for idx, g in enumerate(top, start=1):
            title = g["title"] or f"#{g['id']}"
            lines.append(
                _(
                    "premium-groups-row",
                    rank=idx,
                    title=title,
                    games=g["games_total"],
                )
            )
            if g["invite_link"]:
                rows.append([InlineKeyboardButton(text=f"{idx}. {title}", url=g["invite_link"])])
        rows.append([InlineKeyboardButton(text=_plain("btn-back"), callback_data="inv:back")])
        text = "\n".join(lines)
        kb = InlineKeyboardMarkup(inline_keyboard=rows)

    if query.message:
        with contextlib.suppress(TelegramBadRequest):
            await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")  # type: ignore[union-attr]
    await query.answer()


logger.info("Inventory + shop + exchange handlers loaded")
