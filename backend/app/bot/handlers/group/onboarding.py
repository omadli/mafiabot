"""Onboarding: bot guruhga qo'shilganda til + admin huquqlari sozlash."""

from aiogram import Bot, F, Router
from aiogram.filters import IS_NOT_MEMBER, MEMBER, ChatMemberUpdatedFilter
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from loguru import logger

from app.db.models import Group
from app.db.models.group import (
    DEFAULT_AFK,
    DEFAULT_DISPLAY,
    DEFAULT_GAMEPLAY,
    DEFAULT_ITEMS_ALLOWED,
    DEFAULT_PERMISSIONS,
    DEFAULT_ROLES_ENABLED,
    DEFAULT_SILENCE,
    DEFAULT_TIMINGS,
    GroupSettings,
)
from app.services.i18n_service import get_translator

router = Router(name="group_onboarding")


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> MEMBER))
async def bot_added_to_group(event: ChatMemberUpdated, bot: Bot) -> None:
    """Bot guruhga qo'shildi — onboarding boshlanadi."""
    if event.chat.type not in ("group", "supergroup"):
        return

    # Create group + default settings
    group, _created = await Group.get_or_create(
        id=event.chat.id,
        defaults={"title": event.chat.title or "Group"},
    )
    if not group.title or group.title != event.chat.title:
        group.title = event.chat.title or group.title
        await group.save(update_fields=["title"])

    _settings, _ = await GroupSettings.get_or_create(
        group=group,
        defaults={
            "language": "uz",
            "roles": DEFAULT_ROLES_ENABLED,
            "timings": DEFAULT_TIMINGS,
            "silence": DEFAULT_SILENCE,
            "items_allowed": DEFAULT_ITEMS_ALLOWED,
            "afk": DEFAULT_AFK,
            "permissions": DEFAULT_PERMISSIONS,
            "gameplay": DEFAULT_GAMEPLAY,
            "display": DEFAULT_DISPLAY,
        },
    )

    logger.info(f"Bot added to group {event.chat.id} ({event.chat.title})")

    # Step 1: language picker
    _t = get_translator("uz")  # default for first message
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="onboarding:lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="onboarding:lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="onboarding:lang:en"),
            ]
        ]
    )
    await bot.send_message(
        chat_id=event.chat.id,
        text=_t("onboarding-pick-language"),
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("onboarding:lang:"))
async def onboarding_set_language(query: CallbackQuery, bot: Bot) -> None:
    """Til tanlandi — admin huquqlarini so'rash."""
    if query.data is None or query.message is None:
        await query.answer()
        return

    lang = query.data.removeprefix("onboarding:lang:")
    if lang not in ("uz", "ru", "en"):
        await query.answer("Invalid language", show_alert=True)
        return

    chat_id = query.message.chat.id

    # Verify caller is admin
    member = await bot.get_chat_member(chat_id, query.from_user.id)
    if member.status not in ("creator", "administrator"):
        _t = get_translator(lang)
        await query.answer(_t("onboarding-only-admins-can-pick"), show_alert=True)
        return

    group = await Group.get_or_none(id=chat_id).prefetch_related("settings")
    if group is None or group.settings is None:
        await query.answer("Group not found", show_alert=True)
        return

    group.settings.language = lang
    await group.settings.save(update_fields=["language"])

    _t = get_translator(lang)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_t("btn-check-perms"), callback_data="onboarding:check")]
        ]
    )
    await query.message.edit_text(
        _t("onboarding-grant-admin-perms", bot_username=(await bot.me()).username),
        reply_markup=keyboard,
    )
    await query.answer()


@router.callback_query(F.data == "onboarding:check")
async def onboarding_check_perms(query: CallbackQuery, bot: Bot) -> None:
    """Bot admin huquqlarini tekshirish."""
    if query.message is None:
        await query.answer()
        return

    chat_id = query.message.chat.id
    me = await bot.me()
    bot_member = await bot.get_chat_member(chat_id, me.id)

    has_perms = bot_member.status == "administrator"
    if has_perms:
        delete = getattr(bot_member, "can_delete_messages", False)
        restrict = getattr(bot_member, "can_restrict_members", False)
        pin = getattr(bot_member, "can_pin_messages", False)
    else:
        delete = restrict = pin = False

    group = await Group.get_or_none(id=chat_id).prefetch_related("settings")
    if group is None:
        await query.answer("Group not found", show_alert=True)
        return

    _t = get_translator(group.settings.language if group.settings else "uz")

    if delete and restrict and pin:
        # Save perms and complete onboarding
        group.bot_admin_perms = {
            "delete_messages": True,
            "restrict_members": True,
            "pin_messages": True,
        }
        group.onboarding_completed = True
        await group.save(update_fields=["bot_admin_perms", "onboarding_completed"])

        # Get invite link for "back to group" button
        try:
            link = await bot.export_chat_invite_link(chat_id)
            group.invite_link = link
            await group.save(update_fields=["invite_link"])
        except Exception as e:
            logger.warning(f"Could not export invite link: {e}")

        await query.message.edit_text(_t("onboarding-completed"))
        await query.answer(_t("onboarding-success-toast"), show_alert=False)
    else:
        # Show what's missing
        missing = []
        if not delete:
            missing.append(_t("perm-delete-messages"))
        if not restrict:
            missing.append(_t("perm-restrict-members"))
        if not pin:
            missing.append(_t("perm-pin-messages"))

        await query.answer(
            _t("onboarding-perms-missing", perms=", ".join(missing)),
            show_alert=True,
        )
