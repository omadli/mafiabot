"""Group admin command: /setatmosphere <slot> reply to GIF/video to bind atmosphere media.

Slots: night | day | voting | win_civilian | win_mafia | win_singleton

Only group admins (Telegram permissions) can use this. Saves the file_id to
GroupSettings.atmosphere_media JSON.
"""

from __future__ import annotations

from typing import cast

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loguru import logger

from app.bot.middlewares.i18n import Translator
from app.db.models import Group, GroupSettings, User

router = Router(name="group_atmosphere")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


SLOT_ALIASES = {
    "night": "night_start",
    "day": "day_start",
    "voting": "voting_start",
    "win_civilian": "game_end_civilian_win",
    "win_mafia": "game_end_mafia_win",
    "win_singleton": "game_end_singleton_win",
}


@router.message(Command("setatmosphere"))
async def set_atmosphere(
    message: Message, command: CommandObject, user: User, _: Translator
) -> None:
    """Bind a GIF/video to a phase. Reply to the media with /setatmosphere <slot>.

    Group admin permission required.
    """
    if message.chat.id >= 0:  # not a group
        return

    # Permission check — must be group admin
    member = await message.chat.get_member(user.id)
    if member.status not in ("administrator", "creator"):
        await message.reply(_("atmosphere-admin-only"))
        return

    if command.args is None or command.args.strip() == "":
        slots = " | ".join(SLOT_ALIASES.keys())
        await message.reply(_("atmosphere-help", slots=slots))
        return

    slot_alias = command.args.strip().lower()
    canonical = SLOT_ALIASES.get(slot_alias)
    if canonical is None:
        slots = " | ".join(SLOT_ALIASES.keys())
        await message.reply(_("atmosphere-invalid-slot", slots=slots))
        return

    # Find the replied media
    replied = message.reply_to_message
    if replied is None:
        await message.reply(_("atmosphere-reply-required"))
        return

    file_id: str | None = None
    if replied.animation:
        file_id = replied.animation.file_id
    elif replied.video:
        file_id = replied.video.file_id
    elif replied.video_note:
        file_id = replied.video_note.file_id
    elif (
        replied.document
        and replied.document.mime_type
        and replied.document.mime_type.startswith(("video/", "image/gif"))
    ):
        file_id = replied.document.file_id

    if file_id is None:
        await message.reply(_("atmosphere-no-media"))
        return

    group = await Group.get_or_none(id=message.chat.id).prefetch_related("settings")
    if group is None or group.settings is None:
        await message.reply(_("atmosphere-no-group"))
        return

    settings: GroupSettings = cast(GroupSettings, group.settings)
    media = dict(settings.atmosphere_media or {})
    media[canonical] = file_id
    settings.atmosphere_media = media
    await settings.save(update_fields=["atmosphere_media"])

    logger.info(
        f"Atmosphere media set: group={message.chat.id} slot={canonical} file_id={file_id[:20]}…"
    )
    await message.reply(_("atmosphere-saved", slot=slot_alias))


@router.message(Command("clearatmosphere"))
async def clear_atmosphere(
    message: Message, command: CommandObject, user: User, _: Translator
) -> None:
    """Remove a media binding. /clearatmosphere <slot|all>"""
    if message.chat.id >= 0:
        return

    member = await message.chat.get_member(user.id)
    if member.status not in ("administrator", "creator"):
        await message.reply(_("atmosphere-admin-only"))
        return

    arg = (command.args or "").strip().lower()
    if not arg:
        slots = " | ".join(["all", *SLOT_ALIASES.keys()])
        await message.reply(_("atmosphere-clear-help", slots=slots))
        return

    group = await Group.get_or_none(id=message.chat.id).prefetch_related("settings")
    if group is None or group.settings is None:
        return

    settings: GroupSettings = cast(GroupSettings, group.settings)
    if arg == "all":
        settings.atmosphere_media = {}
    else:
        canonical = SLOT_ALIASES.get(arg)
        if canonical is None:
            slots = " | ".join(SLOT_ALIASES.keys())
            await message.reply(_("atmosphere-invalid-slot", slots=slots))
            return
        media = dict(settings.atmosphere_media or {})
        media.pop(canonical, None)
        settings.atmosphere_media = media

    await settings.save(update_fields=["atmosphere_media"])
    await message.reply(_("atmosphere-cleared", slot=arg))
