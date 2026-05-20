"""/help and /rules commands + Telegram BotCommand menu setup.

These commands intentionally live in private chat only — in group chat
they were just noise (every member could tap them and clutter the chat).
"""

from __future__ import annotations

import contextlib

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from loguru import logger

from app.db.models import User
from app.services.i18n_service import Translator

router = Router(name="common_help")

# Role groupings used in the /rules drill-down. Order matches the
# reference bot's UI; codes match `role-{code}` / `role-desc-{code}` keys.
ROLE_TEAMS: dict[str, list[str]] = {
    "civilians": [
        "citizen",
        "detective",
        "sergeant",
        "mayor",
        "doctor",
        "hooker",
        "hobo",
        "lucky",
        "kamikaze",
    ],
    "mafia": ["don", "mafia", "lawyer", "journalist", "killer"],
    "singletons": [
        "suicide",
        "maniac",
        "werewolf",
        "mage",
        "arsonist",
        "crook",
        "snitch",
    ],
}

# Every role slug from ROLE_TEAMS, used as a membership set for callback
# validation. Real emoji rendering goes through role_config_service via
# the translator (see `_("role-X")` callsites).
_KNOWN_ROLES: frozenset[str] = frozenset(slug for team in ROLE_TEAMS.values() for slug in team)


def _rules_root_keyboard(_: Translator, _plain: Translator | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_plain("btn-rules-roles"), callback_data="rules:teams")],
        ]
    )


def _rules_teams_keyboard(_: Translator, _plain: Translator | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"👨‍👨‍👧‍👦 {_('rules-team-civilians')}",
                    callback_data="rules:team:civilians",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🤵🏼 {_('rules-team-mafia')}",
                    callback_data="rules:team:mafia",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🎯 {_('rules-team-singletons')}",
                    callback_data="rules:team:singletons",
                )
            ],
            [InlineKeyboardButton(text=_plain("btn-rules-back"), callback_data="rules:root")],
        ]
    )


def _rules_role_keyboard(
    team: str, _: Translator, _plain: Translator | None = None
) -> InlineKeyboardMarkup:
    codes = ROLE_TEAMS.get(team, [])
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for code in codes:
        # `_("role-X")` already returns "emoji + name" (dynamic from RoleConfig).
        row.append(
            InlineKeyboardButton(text=_plain(f"role-{code}"), callback_data=f"rules:role:{code}")
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=_plain("btn-rules-back"), callback_data="rules:teams")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _rules_role_detail_keyboard(
    team: str, _: Translator, _plain: Translator | None = None
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_plain("btn-rules-back"), callback_data=f"rules:team:{team}"
                )
            ]
        ]
    )


def _team_for_role(code: str) -> str:
    for team, codes in ROLE_TEAMS.items():
        if code in codes:
            return team
    return "civilians"


async def _safe_edit(query: CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    if query.message is None:
        return
    with contextlib.suppress(TelegramBadRequest):
        await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")  # type: ignore[union-attr]


@router.message(Command("help", prefix="/!"), F.chat.type == "private")
async def cmd_help(
    message: Message, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Help — private chat only."""
    await message.answer(_("help-private"), parse_mode="HTML")


@router.message(Command("rules", prefix="/!"), F.chat.type == "private")
async def cmd_rules(
    message: Message, user: User, _: Translator, _plain: Translator | None = None
) -> None:
    """Rules — opens the detailed rules + role drill-down menu."""
    await message.answer(
        _("rules-summary"),
        reply_markup=_rules_root_keyboard(_, _plain),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "rules:root")
async def cb_rules_root(
    query: CallbackQuery, _: Translator, _plain: Translator | None = None
) -> None:
    await query.answer()
    await _safe_edit(query, _("rules-summary"), _rules_root_keyboard(_, _plain))


@router.callback_query(F.data == "rules:teams")
async def cb_rules_teams(
    query: CallbackQuery, _: Translator, _plain: Translator | None = None
) -> None:
    await query.answer()
    await _safe_edit(query, _("rules-pick-team"), _rules_teams_keyboard(_, _plain))


@router.callback_query(F.data.startswith("rules:team:"))
async def cb_rules_team(
    query: CallbackQuery, _: Translator, _plain: Translator | None = None
) -> None:
    if query.data is None:
        await query.answer()
        return
    team = query.data.split(":")[2]
    if team not in ROLE_TEAMS:
        await query.answer("?", show_alert=True)
        return
    await query.answer()
    text = _(f"rules-team-{team}-intro")
    await _safe_edit(query, text, _rules_role_keyboard(team, _, _plain))


@router.callback_query(F.data.startswith("rules:role:"))
async def cb_rules_role(
    query: CallbackQuery, _: Translator, _plain: Translator | None = None
) -> None:
    if query.data is None:
        await query.answer()
        return
    code = query.data.split(":")[2]
    if code not in _KNOWN_ROLES:
        await query.answer("?", show_alert=True)
        return
    await query.answer()
    # `_("role-X")` already returns "emoji + name". Pass empty emoji to the
    # template so the prefix isn't duplicated.
    role_label = _(f"role-{code}")
    role_desc = _(f"role-desc-{code}")
    text = _(
        "rules-role-detail",
        emoji="",
        role=role_label,
        description=role_desc,
    )
    team = _team_for_role(code)
    await _safe_edit(query, text, _rules_role_detail_keyboard(team, _, _plain))


# === Bot menu setup ===


PRIVATE_COMMANDS = [
    BotCommand(command="start", description="🎮 Botni ishga tushirish"),
    BotCommand(command="profile", description="👤 Profilim"),
    BotCommand(command="inventory", description="🎒 Inventar va do'kon"),
    BotCommand(command="stats", description="📊 Mening statistikam"),
    BotCommand(command="global_top", description="🏆 Global reyting"),
    BotCommand(command="help", description="❓ Yordam"),
    BotCommand(command="rules", description="📖 Qoidalar"),
]


GROUP_COMMANDS = [
    BotCommand(command="game", description="🎲 Yangi o'yin boshlash"),
    BotCommand(command="start", description="▶️ Ro'yxatdagi o'yinni boshlash"),
    BotCommand(command="leave", description="🏃 O'yindan chiqib ketish"),
    BotCommand(command="extend", description="⏱ Vaqtni uzaytirish"),
    BotCommand(command="stop", description="🛑 O'yinni bekor qilish (admin)"),
    BotCommand(command="give", description="💎 Olmos hadya qilish"),
    BotCommand(command="stats", description="📊 Mening statistikam"),
    BotCommand(command="top", description="🏆 Guruh reytingi"),
    BotCommand(command="group_stats", description="📈 Guruh statistikasi"),
    BotCommand(command="profile", description="👤 Profil"),
    BotCommand(command="settings", description="⚙️ Sozlamalar (admin)"),
]


async def setup_bot_commands(bot: Bot) -> None:
    """Register bot commands menu in Telegram (private + group scopes)."""
    try:
        await bot.set_my_commands(PRIVATE_COMMANDS, scope=BotCommandScopeAllPrivateChats())
        await bot.set_my_commands(GROUP_COMMANDS, scope=BotCommandScopeAllGroupChats())
        logger.info("Bot commands menu set up (private + group)")
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")
