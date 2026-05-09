"""Group giveaway commands: /give 50 reply, /give 50 inline."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from loguru import logger

from app.db.models import Giveaway, GiveawayStatus, User
from app.services import giveaway_service
from app.services.i18n_service import Translator
from app.services.messaging import player_mention

router = Router(name="group_giveaway")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


@router.message(Command("give"))
async def cmd_give(
    message: Message, user: User, _: Translator, command: CommandObject, bot: Bot
) -> None:
    """`/give 50` — group giveaway. `/give 50` (reply) — direct gift."""
    if not command.args:
        await message.answer(_("give-amount-required"))
        return
    try:
        amount = int(command.args.strip().split()[0])
    except (ValueError, IndexError):
        await message.answer(_("give-amount-required"))
        return

    if amount < 1:
        await message.answer(_("give-amount-too-small"))
        return

    # Reply → direct gift
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = await User.get_or_none(id=message.reply_to_message.from_user.id)
        if target_user is None:
            await message.answer(_("give-target-not-found"))
            return
        try:
            await giveaway_service.gift_direct(user, target_user, amount)
        except giveaway_service.GiveawayError as e:
            await message.answer(_(str(e)))
            return
        await message.answer(
            _(
                "give-direct-success",
                sender=player_mention(user.id, user.first_name),
                receiver=player_mention(target_user.id, target_user.first_name),
                amount=amount,
            )
        )
        return

    # Group giveaway with inline button
    if user.diamonds < amount:
        await message.answer(_("give-insufficient", have=user.diamonds, need=amount))
        return

    # Send placeholder, then create giveaway with that message_id
    sent = await message.answer(_("give-creating"))
    try:
        gw = await giveaway_service.create_group_giveaway(
            sender=user,
            chat_id=message.chat.id,
            message_id=sent.message_id,
            amount=amount,
            duration_seconds=60,
            max_clicks=10,
            group_id=message.chat.id,
        )
    except giveaway_service.GiveawayError as e:
        await sent.edit_text(_(str(e)))
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("btn-claim-diamond"),
                    callback_data=f"giveaway:click:{gw.id}",
                )
            ]
        ]
    )
    await sent.edit_text(
        _(
            "give-group-message",
            sender=player_mention(user.id, user.first_name),
            amount=amount,
        ),
        reply_markup=keyboard,
    )

    # Schedule finish after expiry (store reference to prevent GC)
    _task = asyncio.create_task(_finish_after_delay(bot, gw.id, gw.chat_id, gw.message_id, _))
    _task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)


async def _finish_after_delay(bot: Bot, giveaway_id, chat_id: int, message_id: int, _) -> None:
    """Wait until giveaway expires, then finalize and edit message."""
    gw = await Giveaway.get(id=giveaway_id)
    delay = (gw.expires_at - datetime.now(UTC)).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay + 1)

    gw_after = await Giveaway.get(id=giveaway_id)
    if gw_after.status != GiveawayStatus.ACTIVE:
        return

    clicks = await giveaway_service.finish_giveaway(giveaway_id)

    # Update group message
    if not clicks:
        text = _("give-no-clicks")
    else:
        lines = []
        for click in clicks:
            await click.fetch_related("user")
            lines.append(
                f"  {click.click_order}. {player_mention(click.user_id, click.user.first_name)} — 💎 {click.diamonds_received}"
            )
        text = _("give-results-header") + "\n" + "\n".join(lines)

    try:
        await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"Could not edit giveaway message: {e}")


@router.callback_query(F.data.startswith("giveaway:click:"))
async def callback_giveaway_click(
    query: CallbackQuery, user: User, _: Translator, bot: Bot
) -> None:
    if query.data is None:
        await query.answer()
        return
    try:
        giveaway_id = query.data.split(":")[2]
    except IndexError:
        await query.answer("Invalid", show_alert=True)
        return

    result = await giveaway_service.click_giveaway(giveaway_id, user)
    if result is None:
        await query.answer(_("giveaway-already-clicked-or-finished"), show_alert=False)
        return

    gw, _click = result
    await query.answer(_("giveaway-clicked-ok"), show_alert=False)

    # If max reached, finalize immediately
    if gw.status == GiveawayStatus.FINISHED:
        await giveaway_service.finish_giveaway(gw.id)
        clicks = await gw.clicks.all().order_by("click_order")
        lines = []
        for c in clicks:
            await c.fetch_related("user")
            lines.append(
                f"  {c.click_order}. {player_mention(c.user_id, c.user.first_name)} — 💎 {c.diamonds_received}"
            )
        text = _("give-results-header") + "\n" + "\n".join(lines)
        try:
            await bot.edit_message_text(text, chat_id=gw.chat_id, message_id=gw.message_id)
        except Exception as e:
            logger.warning(f"Could not edit giveaway message: {e}")
