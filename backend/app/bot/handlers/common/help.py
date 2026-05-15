"""/help and /rules commands + Telegram BotCommand menu setup."""

from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    Message,
)
from loguru import logger

from app.db.models import User
from app.services.i18n_service import Translator

router = Router(name="common_help")


@router.message(Command("help", prefix="/!"))
async def cmd_help(message: Message, user: User, _: Translator) -> None:
    """Help command — context-aware (private vs group)."""
    if message.chat.type == "private":
        await message.answer(_("help-private"))
    else:
        await message.answer(_("help-group"))


@router.message(Command("rules", prefix="/!"))
async def cmd_rules(message: Message, user: User, _: Translator) -> None:
    """Qisqa qoidalar."""
    await message.answer(_("rules-summary"))


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
    BotCommand(command="vote", description="🗳 Ovoz berish"),
    BotCommand(command="extend", description="⏱ Vaqtni uzaytirish"),
    BotCommand(command="stop", description="🛑 O'yinni bekor qilish (admin)"),
    BotCommand(command="give", description="💎 Olmos hadya qilish"),
    BotCommand(command="stats", description="📊 Mening statistikam"),
    BotCommand(command="top", description="🏆 Guruh reytingi"),
    BotCommand(command="group_stats", description="📈 Guruh statistikasi"),
    BotCommand(command="profile", description="👤 Profil"),
    BotCommand(command="settings", description="⚙️ Sozlamalar (admin)"),
    BotCommand(command="rules", description="📖 Qoidalar"),
    BotCommand(command="help", description="❓ Yordam"),
]


async def setup_bot_commands(bot: Bot) -> None:
    """Register bot commands menu in Telegram (private + group scopes)."""
    try:
        await bot.set_my_commands(PRIVATE_COMMANDS, scope=BotCommandScopeAllPrivateChats())
        await bot.set_my_commands(GROUP_COMMANDS, scope=BotCommandScopeAllGroupChats())
        logger.info("Bot commands menu set up (private + group)")
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")
