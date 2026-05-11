"""Private chat group-settings menu (opened via /settings in a group).

Architecture:
  - Top-level menu (`settings:home:<group_id>`) has WebApp button + 6 sub-menus
  - Each sub-menu lets the admin toggle/adjust one section of GroupSettings
  - All callbacks use edit_message_text + answerCallbackQuery
  - All changes persist immediately to GroupSettings JSON columns

Callback namespace: `settings:*`
  settings:home:<gid>
  settings:roles:<gid>
  settings:role:<gid>:<role_code>           — toggle one role
  settings:timings:<gid>
  settings:timing:<gid>:<key>:<delta>       — +/- a timing value
  settings:items:<gid>
  settings:item:<gid>:<code>                — toggle one item
  settings:silence:<gid>
  settings:silence:toggle:<gid>:<key>       — toggle silence rule
  settings:gameplay:<gid>
  settings:gameplay:ratio:<gid>:<low|high>
  settings:gameplay:toggle:<gid>:<key>
  settings:lang:<gid>
  settings:lang:set:<gid>:<lang>
  settings:atmosphere:<gid>                 — info screen (uses /setatmosphere)
"""

from __future__ import annotations

import contextlib

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from loguru import logger

from app.config import settings as app_settings
from app.db.models import Group, GroupSettings, User
from app.db.models.group import (
    DEFAULT_GAMEPLAY,
    DEFAULT_ITEMS_ALLOWED,
    DEFAULT_ROLES_ENABLED,
    DEFAULT_SILENCE,
    DEFAULT_TIMINGS,
)
from app.services.i18n_service import Translator, get_translator

router = Router(name="private_group_settings")

# === Constants ===

# Filter: private chats only
router.callback_query.filter(F.message.chat.type == "private")

ROLE_GROUPS: dict[str, list[str]] = {
    "civilians": [
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
    ],
    "mafia": ["don", "mafia", "lawyer", "journalist", "killer"],
    "singletons": ["maniac", "werewolf", "mage", "arsonist", "crook", "snitch"],
}

ITEM_LABELS = {
    "shield": "🛡 Himoya",
    "killer_shield": "⛑ Qotildan himoya",
    "vote_shield": "⚖️ Ovoz himoyasi",
    "rifle": "🔫 Miltiq",
    "mask": "🎭 Maska",
    "fake_document": "📁 Soxta hujjat",
}

SILENCE_KEYS = ["dead_players", "sleeping_players", "non_players", "night_chat"]

# Timing display order + per-tap delta seconds
TIMING_KEYS: list[tuple[str, int]] = [
    ("registration", 30),
    ("night", 15),
    ("day", 15),
    ("mafia_vote", 5),
    ("hanging_vote", 5),
    ("hanging_confirm", 5),
    ("last_words", 5),
    ("afsungar_carry", 5),
]


# === Helpers ===


def _webapp_url(start_param: str | None = None) -> str:
    """Build WebApp URL (host-served by nginx)."""
    base = f"https://{app_settings.public_domain}/webapp/"
    if start_param:
        base += f"?start={start_param}"
    return base


async def _edit(query: CallbackQuery, text: str, markup, parse_mode: str | None = "HTML") -> None:
    if query.message is None:
        return
    with contextlib.suppress(TelegramBadRequest):
        await query.message.edit_text(text, reply_markup=markup, parse_mode=parse_mode)


async def _load_group_or_fail(
    query: CallbackQuery, group_id: int
) -> tuple[Group | None, GroupSettings | None]:
    group = await Group.get_or_none(id=group_id).prefetch_related("settings")
    if group is None:
        await query.answer("Group not found", show_alert=True)
        return None, None
    s = await GroupSettings.get_or_none(group_id=group_id)
    if s is None:
        await query.answer("Settings not found", show_alert=True)
        return None, None
    return group, s


def _toggle_label(enabled: bool) -> str:
    return "🟢 ON" if enabled else "🔴 OFF"


# === Top-level (home) menu ===


async def build_settings_home_message(
    group: Group, s: GroupSettings, _: Translator
) -> tuple[str, InlineKeyboardMarkup]:
    """Top-level settings menu — WebApp deeplink + 6 sub-menus."""
    title = group.title or f"#{group.id}"
    text = _("settings-home", group_title=title)

    rows: list[list[InlineKeyboardButton]] = []

    # WebApp shortcuts (Telegram native UI)
    rows.append(
        [
            InlineKeyboardButton(
                text=_("btn-settings-webapp"),
                web_app=WebAppInfo(url=_webapp_url(f"settings_{group.id}")),
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=_("btn-settings-history"),
                web_app=WebAppInfo(url=_webapp_url(f"history_{group.id}")),
            )
        ]
    )

    # Bot-side sub-menus
    rows.append(
        [
            InlineKeyboardButton(
                text=_("btn-settings-roles"), callback_data=f"settings:roles:{group.id}"
            ),
            InlineKeyboardButton(
                text=_("btn-settings-timings"), callback_data=f"settings:timings:{group.id}"
            ),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=_("btn-settings-items"), callback_data=f"settings:items:{group.id}"
            ),
            InlineKeyboardButton(
                text=_("btn-settings-silence"), callback_data=f"settings:silence:{group.id}"
            ),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=_("btn-settings-gameplay"), callback_data=f"settings:gameplay:{group.id}"
            ),
            InlineKeyboardButton(
                text=_("btn-settings-lang"), callback_data=f"settings:lang:{group.id}"
            ),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=_("btn-settings-atmosphere"), callback_data=f"settings:atmosphere:{group.id}"
            )
        ]
    )

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("settings:home:"))
async def cb_home(query: CallbackQuery, user: User, _: Translator) -> None:
    gid = int(query.data.split(":")[2])
    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return
    await query.answer()
    text, kb = await build_settings_home_message(group, s, _)
    await _edit(query, text, kb)


# === Roles sub-menu ===


def _build_roles_kb(s: GroupSettings, gid: int, _: Translator) -> InlineKeyboardMarkup:
    roles_state = {**DEFAULT_ROLES_ENABLED, **(s.roles or {})}
    rows: list[list[InlineKeyboardButton]] = []

    for team, codes in ROLE_GROUPS.items():
        # Team header (non-clickable)
        rows.append(
            [InlineKeyboardButton(text=_(f"settings-team-{team}"), callback_data="settings:noop")]
        )
        row: list[InlineKeyboardButton] = []
        for code in codes:
            emoji_name = _(f"role-{code}")  # "🛡 Citizen" etc.
            enabled = roles_state.get(code, False)
            label = f"{_toggle_label(enabled)} {emoji_name}"
            row.append(
                InlineKeyboardButton(text=label, callback_data=f"settings:role:{gid}:{code}")
            )
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)

    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data=f"settings:home:{gid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("settings:roles:"))
async def cb_roles(query: CallbackQuery, user: User, _: Translator) -> None:
    gid = int(query.data.split(":")[2])
    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return
    await query.answer()
    await _edit(query, _("settings-roles-prompt"), _build_roles_kb(s, gid, _))


@router.callback_query(F.data.startswith("settings:role:"))
async def cb_role_toggle(query: CallbackQuery, user: User, _: Translator) -> None:
    parts = query.data.split(":")
    if len(parts) != 4:
        await query.answer("Invalid", show_alert=True)
        return
    gid = int(parts[2])
    code = parts[3]

    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return

    roles = {**DEFAULT_ROLES_ENABLED, **(s.roles or {})}
    new_state = not roles.get(code, False)
    roles[code] = new_state
    s.roles = roles
    await s.save(update_fields=["roles"])

    emoji_name = _(f"role-{code}")
    await query.answer(f"{emoji_name}: {_toggle_label(new_state)}")
    await _edit(query, _("settings-roles-prompt"), _build_roles_kb(s, gid, _))


# === Timings sub-menu ===


def _build_timings_text(s: GroupSettings, _: Translator) -> str:
    t = {**DEFAULT_TIMINGS, **(s.timings or {})}
    lines = [_("settings-timings-prompt"), ""]
    for key, _delta in TIMING_KEYS:
        lines.append(f"  {_(f'timing-{key}')}: <b>{t.get(key, 0)}s</b>")
    return "\n".join(lines)


def _build_timings_kb(s: GroupSettings, gid: int, _: Translator) -> InlineKeyboardMarkup:
    t = {**DEFAULT_TIMINGS, **(s.timings or {})}
    rows: list[list[InlineKeyboardButton]] = []
    for key, delta in TIMING_KEYS:
        current = t.get(key, 0)
        label = f"{_(f'timing-{key}')}  {current}s"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"➖ {delta}", callback_data=f"settings:timing:{gid}:{key}:-{delta}"
                ),
                InlineKeyboardButton(text=label, callback_data="settings:noop"),
                InlineKeyboardButton(
                    text=f"➕ {delta}", callback_data=f"settings:timing:{gid}:{key}:{delta}"
                ),
            ]
        )
    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data=f"settings:home:{gid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("settings:timings:"))
async def cb_timings(query: CallbackQuery, user: User, _: Translator) -> None:
    gid = int(query.data.split(":")[2])
    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return
    await query.answer()
    await _edit(query, _build_timings_text(s, _), _build_timings_kb(s, gid, _))


@router.callback_query(F.data.startswith("settings:timing:"))
async def cb_timing_adjust(query: CallbackQuery, user: User, _: Translator) -> None:
    parts = query.data.split(":")
    if len(parts) != 5:
        await query.answer("Invalid", show_alert=True)
        return
    gid = int(parts[2])
    key = parts[3]
    try:
        delta = int(parts[4])
    except ValueError:
        await query.answer("Invalid", show_alert=True)
        return

    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return

    t = {**DEFAULT_TIMINGS, **(s.timings or {})}
    new_val = max(5, min(900, t.get(key, 0) + delta))  # clamp 5..900s
    t[key] = new_val
    s.timings = t
    await s.save(update_fields=["timings"])

    await query.answer(f"{_(f'timing-{key}')}: {new_val}s")
    await _edit(query, _build_timings_text(s, _), _build_timings_kb(s, gid, _))


# === Items sub-menu ===


def _build_items_kb(s: GroupSettings, gid: int, _: Translator) -> InlineKeyboardMarkup:
    items = {**DEFAULT_ITEMS_ALLOWED, **(s.items_allowed or {})}
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for code, label in ITEM_LABELS.items():
        enabled = items.get(code, False)
        btn_label = f"{_toggle_label(enabled)} {label}"
        row.append(
            InlineKeyboardButton(text=btn_label, callback_data=f"settings:item:{gid}:{code}")
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data=f"settings:home:{gid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("settings:items:"))
async def cb_items(query: CallbackQuery, user: User, _: Translator) -> None:
    gid = int(query.data.split(":")[2])
    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return
    await query.answer()
    await _edit(query, _("settings-items-prompt"), _build_items_kb(s, gid, _))


@router.callback_query(F.data.startswith("settings:item:"))
async def cb_item_toggle(query: CallbackQuery, user: User, _: Translator) -> None:
    parts = query.data.split(":")
    if len(parts) != 4:
        await query.answer("Invalid", show_alert=True)
        return
    gid = int(parts[2])
    code = parts[3]

    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return

    items = {**DEFAULT_ITEMS_ALLOWED, **(s.items_allowed or {})}
    items[code] = not items.get(code, False)
    s.items_allowed = items
    await s.save(update_fields=["items_allowed"])

    await query.answer(f"{ITEM_LABELS.get(code, code)}: {_toggle_label(items[code])}")
    await _edit(query, _("settings-items-prompt"), _build_items_kb(s, gid, _))


# === Silence sub-menu ===


def _build_silence_kb(s: GroupSettings, gid: int, _: Translator) -> InlineKeyboardMarkup:
    silence = {**DEFAULT_SILENCE, **(s.silence or {})}
    rows: list[list[InlineKeyboardButton]] = []
    for key in SILENCE_KEYS:
        enabled = silence.get(key, False)
        label = f"{_toggle_label(enabled)} {_(f'silence-{key}')}"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"settings:silence:toggle:{gid}:{key}")]
        )
    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data=f"settings:home:{gid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.regexp(r"^settings:silence:\d+$"))
async def cb_silence(query: CallbackQuery, user: User, _: Translator) -> None:
    gid = int(query.data.split(":")[2])
    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return
    await query.answer()
    await _edit(query, _("settings-silence-prompt"), _build_silence_kb(s, gid, _))


@router.callback_query(F.data.startswith("settings:silence:toggle:"))
async def cb_silence_toggle(query: CallbackQuery, user: User, _: Translator) -> None:
    parts = query.data.split(":")
    if len(parts) != 5:
        await query.answer("Invalid", show_alert=True)
        return
    gid = int(parts[3])
    key = parts[4]

    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return

    silence = {**DEFAULT_SILENCE, **(s.silence or {})}
    silence[key] = not silence.get(key, False)
    s.silence = silence
    await s.save(update_fields=["silence"])

    await query.answer(f"{_(f'silence-{key}')}: {_toggle_label(silence[key])}")
    await _edit(query, _("settings-silence-prompt"), _build_silence_kb(s, gid, _))


# === Gameplay sub-menu ===


def _build_gameplay_text(s: GroupSettings, _: Translator) -> str:
    g = {**DEFAULT_GAMEPLAY, **(s.gameplay or {})}
    return _(
        "settings-gameplay-status",
        ratio=g.get("mafia_ratio", "low"),
        min_players=g.get("min_players", 4),
        max_players=g.get("max_players", 30),
        skip_day_vote=_toggle_label(g.get("allow_skip_day_vote", True)),
        skip_night_action=_toggle_label(g.get("allow_skip_night_action", True)),
    )


def _build_gameplay_kb(s: GroupSettings, gid: int, _: Translator) -> InlineKeyboardMarkup:
    g = {**DEFAULT_GAMEPLAY, **(s.gameplay or {})}
    ratio = g.get("mafia_ratio", "low")

    rows = [
        [
            InlineKeyboardButton(
                text=("🟢 " if ratio == "low" else "  ") + _("gameplay-ratio-low"),
                callback_data=f"settings:gameplay:ratio:{gid}:low",
            ),
            InlineKeyboardButton(
                text=("🟢 " if ratio == "high" else "  ") + _("gameplay-ratio-high"),
                callback_data=f"settings:gameplay:ratio:{gid}:high",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{_toggle_label(g.get('allow_skip_day_vote', True))} {_('gameplay-skip-day')}",
                callback_data=f"settings:gameplay:toggle:{gid}:allow_skip_day_vote",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{_toggle_label(g.get('allow_skip_night_action', True))} {_('gameplay-skip-night')}",
                callback_data=f"settings:gameplay:toggle:{gid}:allow_skip_night_action",
            )
        ],
        [InlineKeyboardButton(text=_("btn-back"), callback_data=f"settings:home:{gid}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.regexp(r"^settings:gameplay:\d+$"))
async def cb_gameplay(query: CallbackQuery, user: User, _: Translator) -> None:
    gid = int(query.data.split(":")[2])
    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return
    await query.answer()
    await _edit(query, _build_gameplay_text(s, _), _build_gameplay_kb(s, gid, _))


@router.callback_query(F.data.startswith("settings:gameplay:ratio:"))
async def cb_gameplay_ratio(query: CallbackQuery, user: User, _: Translator) -> None:
    parts = query.data.split(":")
    if len(parts) != 5:
        await query.answer("Invalid", show_alert=True)
        return
    gid = int(parts[3])
    ratio = parts[4]
    if ratio not in ("low", "high"):
        await query.answer("Invalid", show_alert=True)
        return

    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return

    g = {**DEFAULT_GAMEPLAY, **(s.gameplay or {})}
    g["mafia_ratio"] = ratio
    s.gameplay = g
    await s.save(update_fields=["gameplay"])

    await query.answer(f"{_('gameplay-ratio-' + ratio)} ✓")
    await _edit(query, _build_gameplay_text(s, _), _build_gameplay_kb(s, gid, _))


@router.callback_query(F.data.startswith("settings:gameplay:toggle:"))
async def cb_gameplay_toggle(query: CallbackQuery, user: User, _: Translator) -> None:
    parts = query.data.split(":")
    if len(parts) != 5:
        await query.answer("Invalid", show_alert=True)
        return
    gid = int(parts[3])
    key = parts[4]
    if key not in ("allow_skip_day_vote", "allow_skip_night_action"):
        await query.answer("Invalid", show_alert=True)
        return

    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return

    g = {**DEFAULT_GAMEPLAY, **(s.gameplay or {})}
    g[key] = not g.get(key, False)
    s.gameplay = g
    await s.save(update_fields=["gameplay"])

    await query.answer(
        f"{_('gameplay-' + key.replace('allow_skip_', 'skip-').replace('_', '-'))}: {_toggle_label(g[key])}"
    )
    await _edit(query, _build_gameplay_text(s, _), _build_gameplay_kb(s, gid, _))


# === Language sub-menu (group locale) ===


def _build_lang_kb(s: GroupSettings, gid: int, _: Translator) -> InlineKeyboardMarkup:
    current = s.language
    options = [("uz", "🇺🇿 O'zbekcha"), ("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English")]
    rows = [
        [
            InlineKeyboardButton(
                text=("🟢 " if code == current else "  ") + label,
                callback_data=f"settings:lang:set:{gid}:{code}",
            )
        ]
        for code, label in options
    ]
    rows.append([InlineKeyboardButton(text=_("btn-back"), callback_data=f"settings:home:{gid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.regexp(r"^settings:lang:\d+$"))
async def cb_lang(query: CallbackQuery, user: User, _: Translator) -> None:
    gid = int(query.data.split(":")[2])
    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return
    await query.answer()
    await _edit(query, _("settings-lang-prompt"), _build_lang_kb(s, gid, _))


@router.callback_query(F.data.startswith("settings:lang:set:"))
async def cb_lang_set(query: CallbackQuery, user: User, _: Translator) -> None:
    parts = query.data.split(":")
    if len(parts) != 5:
        await query.answer("Invalid", show_alert=True)
        return
    gid = int(parts[3])
    new_lang = parts[4]
    if new_lang not in ("uz", "ru", "en"):
        await query.answer("Invalid", show_alert=True)
        return

    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return

    s.language = new_lang
    await s.save(update_fields=["language"])
    new_t = get_translator(new_lang)
    await query.answer(new_t("language-switched"))
    await _edit(query, new_t("settings-lang-prompt"), _build_lang_kb(s, gid, new_t))


# === Atmosphere info screen ===


@router.callback_query(F.data.startswith("settings:atmosphere:"))
async def cb_atmosphere(query: CallbackQuery, user: User, _: Translator) -> None:
    gid = int(query.data.split(":")[2])
    group, s = await _load_group_or_fail(query, gid)
    if group is None or s is None:
        return
    await query.answer()

    media = s.atmosphere_media or {}
    lines = [_("settings-atmosphere-info"), ""]
    for slot in (
        "night_start",
        "day_start",
        "voting_start",
        "game_end_civilian_win",
        "game_end_mafia_win",
    ):
        marker = "🟢" if media.get(slot) else "⚪"
        lines.append(f"  {marker} <code>{slot}</code>")
    text = "\n".join(lines)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("btn-back"), callback_data=f"settings:home:{gid}")],
        ]
    )
    await _edit(query, text, kb)


# === No-op (clicked header / spacer) ===


@router.callback_query(F.data == "settings:noop")
async def cb_noop(query: CallbackQuery) -> None:
    await query.answer()


logger.info("Group-settings handlers loaded")
