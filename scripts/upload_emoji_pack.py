"""Upload generated WebM emojis to Telegram as a custom-emoji sticker set.

The pack is owned by the first super-admin Telegram user_id from .env. The
pack name must end with `_by_<bot_username>`; this script appends it.

Run:
  python scripts/upload_emoji_pack.py                          # default name
  python scripts/upload_emoji_pack.py --name mafia_uz_emojis   # custom slug
  python scripts/upload_emoji_pack.py --title "Mafia O'yini"   # custom title
  python scripts/upload_emoji_pack.py --add-only               # add to existing pack
  python scripts/upload_emoji_pack.py --delete                 # tear down the pack

The script is idempotent on the "add" path — if the pack already exists, new
emojis are appended; existing ones are skipped (Telegram errors out cleanly).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Windows console UTF-8
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from aiogram import Bot  # noqa: E402
from aiogram.exceptions import TelegramBadRequest  # noqa: E402
from aiogram.types import FSInputFile, InputSticker  # noqa: E402

from app.config import settings  # noqa: E402

EMOJI_DIR = ROOT / "scripts" / "output" / "emoji"

# Order matters — name → unicode anchor emoji (Telegram requires every custom
# emoji to map to at least one standard Unicode emoji for keyword search).
PACK_EMOJIS: dict[str, list[str]] = {
    # Scene / shared
    "card":       ["🃏", "🎴"],
    "moon":       ["🌙", "🌛", "🌃"],
    "sun":        ["🌅", "☀️", "🌄"],
    "skull":      ["💀", "☠️"],
    "shield":     ["🛡", "🛡️"],
    "trophy":     ["🏆", "🥇"],
    "knife":      ["🔪", "🗡"],
    # Civilians (10)
    "citizen":    ["👨🏼", "👤", "🙂"],
    "detective":  ["🕵🏻‍♂", "🔍"],
    "sergeant":   ["👮🏻‍♂", "⭐"],
    "mayor":      ["🎖", "🥇"],
    "doctor":     ["👨🏻‍⚕", "⚕️", "➕"],
    "hooker":     ["💃", "💋", "❤️"],
    "hobo":       ["🚶‍♂", "🚶", "🧙‍♂"],
    "lucky":      ["🤞🏼", "🍀"],
    "suicide":    ["🤦🏼", "😵", "😢"],
    "kamikaze":   ["💣", "🔥"],
    # Mafia (5)
    "don":        ["🤵🏻", "🎩", "💨"],
    "mafia":      ["🤵🏼", "🤵", "🥸"],
    "lawyer":     ["👨‍💼", "⚖️", "🔨"],
    "journalist": ["📸", "📷", "👩🏼‍💻"],
    "ninja":      ["🥷", "🌟"],
    # Singletons (6)
    "maniac":     ["👹", "🎭", "👺"],
    "werewolf":   ["🐺"],
    "mage":       ["🧙", "✨"],
    "arsonist":   ["🔥", "🧟", "💥"],
    "crook":      ["🤹", "🎴"],
    "snitch":     ["🐀", "🤓", "🗣"],
}


def _owner_user_id() -> int:
    ids = settings.super_admin_ids
    if not ids:
        sys.exit(
            "SUPER_ADMIN_TELEGRAM_IDS is empty in .env — set at least one ID "
            "(the Telegram user who will own the emoji pack)."
        )
    return next(iter(ids))


def _pack_name(slug: str, bot_username: str) -> str:
    suffix = f"_by_{bot_username}"
    name = slug if slug.endswith(suffix) else f"{slug}{suffix}"
    # Telegram pack names: alphanumeric + underscores, 1..64 chars
    if not all(c.isalnum() or c == "_" for c in name):
        sys.exit(f"Invalid pack name {name!r} — alphanumeric + underscores only")
    if len(name) > 64:
        sys.exit(f"Pack name too long ({len(name)} > 64): {name!r}")
    return name


async def _wait_for_pack(bot: Bot, name: str, attempts: int = 30,
                          delay: float = 1.0) -> None:
    """Poll get_sticker_set until the named pack is visible."""
    for _ in range(attempts):
        try:
            await bot.get_sticker_set(name=name)
            return
        except TelegramBadRequest:
            await asyncio.sleep(delay)
    raise RuntimeError(f"Pack {name!r} did not become available after "
                       f"{attempts * delay:.0f}s")


async def _add_one(bot: Bot, user_id: int, name: str, emoji_name: str,
                    anchors: list[str], retries: int = 8) -> None:
    """Add one sticker, retrying STICKERSET_INVALID until propagation settles."""
    webm = EMOJI_DIR / f"{emoji_name}.webm"
    if not webm.exists():
        print(f"  ⚠️  skipped {emoji_name}: file missing")
        return
    for attempt in range(retries):
        try:
            await bot.add_sticker_to_set(
                user_id=user_id,
                name=name,
                sticker=InputSticker(
                    sticker=FSInputFile(webm),
                    format="video",
                    emoji_list=anchors,
                ),
            )
            print(f"  ✅ {emoji_name}.webm — {', '.join(anchors)}")
            return
        except TelegramBadRequest as e:
            if "STICKERSET_INVALID" in e.message and attempt < retries - 1:
                # exponential backoff: 2, 4, 6, 8, 10, 12, 14 seconds
                await asyncio.sleep(2 * (attempt + 1))
                continue
            print(f"  ❌ {emoji_name}: {e.message}")
            return


async def _create(bot: Bot, user_id: int, name: str, title: str) -> None:
    items = list(PACK_EMOJIS.items())
    first_name, first_emoji = items[0]
    first_file = EMOJI_DIR / f"{first_name}.webm"
    if not first_file.exists():
        sys.exit(f"Missing {first_file} — run generate_custom_emojis.py first")

    print(f"→ Creating pack {name!r} (owner user_id={user_id})")
    await bot.create_new_sticker_set(
        user_id=user_id,
        name=name,
        title=title,
        stickers=[
            InputSticker(
                sticker=FSInputFile(first_file),
                format="video",
                emoji_list=first_emoji,
            )
        ],
        sticker_type="custom_emoji",
    )
    print(f"  ✅ {first_name}.webm — {', '.join(first_emoji)}")

    # Wait for Telegram to fully register the pack, then a long buffer.
    # Empirically the create call returns optimistically and add_sticker_to_set
    # rejects with STICKERSET_INVALID for the first ~10-15s.
    await _wait_for_pack(bot, name)
    print("  ⏳ waiting 20s for Telegram pack propagation…")
    await asyncio.sleep(20)

    for emoji_name, anchors in items[1:]:
        await _add_one(bot, user_id, name, emoji_name, anchors)


async def _add_only(bot: Bot, user_id: int, name: str) -> None:
    """Append emojis to an existing pack, skipping ones whose primary
    anchor emoji is already there. Telegram does NOT dedupe video custom
    emoji uploads by content, so we must dedupe ourselves."""
    try:
        set_info = await bot.get_sticker_set(name=name)
    except TelegramBadRequest as e:
        sys.exit(f"Pack {name!r} not found: {e.message}")

    present: set[str] = {s.emoji for s in set_info.stickers if s.emoji}
    print(f"→ Pack {name!r} has {len(set_info.stickers)} sticker(s); "
          f"appending only ones whose anchor isn't already in pack")

    for emoji_name, anchors in PACK_EMOJIS.items():
        if anchors and anchors[0] in present:
            print(f"  ⊝ skipped {emoji_name} (anchor {anchors[0]} already in pack)")
            continue
        await _add_one(bot, user_id, name, emoji_name, anchors)
        if anchors:
            present.add(anchors[0])


async def _delete(bot: Bot, name: str) -> None:
    try:
        await bot.delete_sticker_set(name=name)
        print(f"✅ deleted {name}")
    except TelegramBadRequest as e:
        sys.exit(f"Failed to delete {name}: {e.message}")


async def _run(args: argparse.Namespace) -> None:
    bot = Bot(token=settings.bot_token.get_secret_value())
    try:
        me = await bot.get_me()
        if not me.username:
            sys.exit("Bot has no username — set one via @BotFather first")
        pack_name = _pack_name(args.name, me.username)
        owner = _owner_user_id()

        if args.delete:
            await _delete(bot, pack_name)
            return
        if args.add_only:
            await _add_only(bot, owner, pack_name)
        else:
            await _create(bot, owner, pack_name, args.title)

        print()
        print(f"🔗 Open pack: https://t.me/addemoji/{pack_name}")
    finally:
        await bot.session.close()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--name", default="mafia_uz",
                   help="Pack slug; '_by_<bot_username>' is auto-appended")
    p.add_argument("--title", default="Mafia O'yini",
                   help="Human-readable pack title")
    p.add_argument("--add-only", action="store_true",
                   help="Append to an existing pack instead of creating")
    p.add_argument("--delete", action="store_true",
                   help="Delete the pack entirely (irreversible)")
    args = p.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
