"""One-shot: push the bot's profile texts (name / about / description) to Telegram.

Run from project root:

    python scripts/setup_bot_profile.py            # apply
    python scripts/setup_bot_profile.py --dry-run  # preview only

Reads BOT_TOKEN from .env (via the existing pydantic settings). Sets the
"default" locale entry (empty language_code), which Telegram shows to every
user whose Telegram UI language has no specific override.

Telegram Bot API limits:
  setMyName              — name,              max  64 chars
  setMyShortDescription  — about (profile),   max 120 chars
  setMyDescription       — description (chat empty), max 512 chars

Photos (bot profile pic + description picture) cannot be set via Bot API.
Use @BotFather:
  /mybots → @MafGameUzBot → Edit Bot → Edit Botpic
  /mybots → @MafGameUzBot → Edit Bot → Edit Description Picture
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Windows consoles default to cp1251/cp866 and choke on emoji / box-drawing.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# Make `backend/app` importable so we reuse the existing Settings loader.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))

from aiogram import Bot  # noqa: E402

from app.config import settings  # noqa: E402

NAME = "🃏 Mafia | Telegram guruh o'yini"

SHORT_DESCRIPTION = (
    "🎭 Telegramda klassik Mafia o'yini. 4–30 o'yinchi, 21+ rol. "
    "Meni guruhga qo'shing va /game bilan boshlang."
)

DESCRIPTION = (
    "🃏 Salom! Men Mafia o'yini botiman.\n"
    "\n"
    "🎭 Imkoniyatlar:\n"
    "• 4–30 o'yinchi uchun klassik Mafia\n"
    "• 21+ noyob rol: Don, Komissar, Doktor, Sehrgar, Qotil…\n"
    "• 🔫 Qurol, 🛡 himoya, 🎒 inventar\n"
    "• 📊 Statistika, 🏆 ELO reyting, achievement'lar\n"
    "• 💎 Olmos giveaway va premium imkoniyatlar\n"
    "• 🇺🇿 / 🇷🇺 / 🇬🇧 — uch til\n"
    "\n"
    "🚀 Boshlash:\n"
    "1. Meni guruhga qo'shing va admin qiling\n"
    "2. /game yozing\n"
    "3. Bugun kim Don, kim Komissar — bilib oling!\n"
    "\n"
    "📢 @Mafiauzbot_news"
)


def _check_limits() -> None:
    """Fail fast if any payload exceeds Telegram's limits."""
    problems: list[str] = []
    if len(NAME) > 64:
        problems.append(f"NAME is {len(NAME)} chars, max 64")
    if len(SHORT_DESCRIPTION) > 120:
        problems.append(f"SHORT_DESCRIPTION is {len(SHORT_DESCRIPTION)} chars, max 120")
    if len(DESCRIPTION) > 512:
        problems.append(f"DESCRIPTION is {len(DESCRIPTION)} chars, max 512")
    if problems:
        raise SystemExit("Limit check failed:\n  - " + "\n  - ".join(problems))


def _preview() -> None:
    bar = "─" * 72
    print(bar)
    print(f"NAME              ({len(NAME):>3}/64 chars)")
    print(f"  {NAME}")
    print(bar)
    print(f"SHORT DESCRIPTION ({len(SHORT_DESCRIPTION):>3}/120 chars) — shown on bot profile")
    print(f"  {SHORT_DESCRIPTION}")
    print(bar)
    print(f"DESCRIPTION       ({len(DESCRIPTION):>3}/512 chars) — shown when chat is empty")
    for line in DESCRIPTION.splitlines() or [""]:
        print(f"  {line}")
    print(bar)


async def _apply() -> None:
    bot = Bot(token=settings.bot_token.get_secret_value())
    try:
        me = await bot.get_me()
        print(f"→ Target bot: @{me.username} (id={me.id})")

        await bot.set_my_name(name=NAME)
        print("✅ setMyName")

        await bot.set_my_short_description(short_description=SHORT_DESCRIPTION)
        print("✅ setMyShortDescription")

        await bot.set_my_description(description=DESCRIPTION)
        print("✅ setMyDescription")
    finally:
        await bot.session.close()

    print()
    print("Photos must be set via @BotFather (no Bot API method exists):")
    print("  1. Open @BotFather → /mybots → @" + (me.username or "MafGameUzBot"))
    print("  2. Edit Bot → Edit Botpic              → upload square (≥640×640) PNG/JPG")
    print("  3. Edit Bot → Edit Description Picture → upload landscape image or short MP4/GIF")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the payload without calling Telegram",
    )
    args = parser.parse_args()

    _check_limits()
    _preview()

    if args.dry_run:
        print("\n(dry-run: nothing sent to Telegram)")
        return

    asyncio.run(_apply())


if __name__ == "__main__":
    main()
