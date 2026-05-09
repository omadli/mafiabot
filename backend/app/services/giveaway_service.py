"""Giveaway service — /give logic (reply, inline, harmonic distribution)."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from uuid import UUID

from loguru import logger
from tortoise.transactions import in_transaction

from app.db.models import (
    Giveaway,
    GiveawayClick,
    GiveawayStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
)


class GiveawayError(Exception):
    """Domain error from giveaway service (i18n key)."""


# === 1. Reply-based direct gift ===


async def gift_direct(sender: User, receiver: User, amount: int) -> None:
    """Atomically transfer diamonds from sender to receiver."""
    if amount < 1:
        raise GiveawayError("give-amount-too-small")
    if sender.id == receiver.id:
        raise GiveawayError("give-cannot-self")

    async with in_transaction():
        sender_locked = await User.select_for_update().get(id=sender.id)
        if sender_locked.diamonds < amount:
            raise GiveawayError("give-insufficient")

        sender_locked.diamonds -= amount
        await sender_locked.save(update_fields=["diamonds"])

        receiver_locked = await User.select_for_update().get(id=receiver.id)
        receiver_locked.diamonds += amount
        await receiver_locked.save(update_fields=["diamonds"])

        await Transaction.create(
            user=sender_locked,
            type=TransactionType.GIFT_SEND,
            diamonds_amount=-amount,
            counterparty=receiver_locked,
            status=TransactionStatus.COMPLETED,
        )
        await Transaction.create(
            user=receiver_locked,
            type=TransactionType.GIFT_RECEIVE,
            diamonds_amount=amount,
            counterparty=sender_locked,
            status=TransactionStatus.COMPLETED,
        )

    logger.info(f"Gift: {sender.id} → {receiver.id}: {amount} diamonds")


# === 2. Group giveaway with inline button ===


async def create_group_giveaway(
    sender: User,
    chat_id: int,
    message_id: int,
    amount: int,
    duration_seconds: int = 60,
    max_clicks: int = 10,
    group_id: int | None = None,
) -> Giveaway:
    """Create a group giveaway. Sender's diamonds are reserved (debited)."""
    if amount < 1:
        raise GiveawayError("give-amount-too-small")

    async with in_transaction():
        sender_locked = await User.select_for_update().get(id=sender.id)
        if sender_locked.diamonds < amount:
            raise GiveawayError("give-insufficient")

        sender_locked.diamonds -= amount
        await sender_locked.save(update_fields=["diamonds"])

        giveaway = await Giveaway.create(
            sender=sender_locked,
            group_id=group_id,
            chat_id=chat_id,
            message_id=message_id,
            total_diamonds=amount,
            expires_at=datetime.now(UTC) + timedelta(seconds=duration_seconds),
            max_clicks=max_clicks,
            status=GiveawayStatus.ACTIVE,
        )

        await Transaction.create(
            user=sender_locked,
            type=TransactionType.SPEND_DIAMONDS,
            diamonds_amount=-amount,
            related_giveaway_id=giveaway.id,
            status=TransactionStatus.COMPLETED,
            note="Giveaway escrow",
        )

    logger.info(f"Giveaway {giveaway.id} created by {sender.id} ({amount} diamonds)")
    return giveaway


async def click_giveaway(giveaway_id: UUID, user: User) -> tuple[Giveaway, GiveawayClick] | None:
    """Register a click. Returns (giveaway, click) or None if invalid.

    Diamonds are NOT credited yet — they're paid out at finish_giveaway().
    """
    async with in_transaction():
        giveaway = await Giveaway.select_for_update().get(id=giveaway_id)
        if giveaway.status != GiveawayStatus.ACTIVE:
            return None
        if datetime.now(UTC) > giveaway.expires_at:
            return None
        if giveaway.sender_id == user.id:
            return None  # self-click not allowed

        # Already clicked?
        existing = await GiveawayClick.get_or_none(giveaway_id=giveaway_id, user_id=user.id)
        if existing is not None:
            return None

        # Click order
        click_count = await GiveawayClick.filter(giveaway_id=giveaway_id).count()
        if click_count >= giveaway.max_clicks:
            return None

        click = await GiveawayClick.create(
            giveaway_id=giveaway_id,
            user=user,
            click_order=click_count + 1,
            diamonds_received=0,  # set on finish
        )

        # If max reached → finish
        if click_count + 1 >= giveaway.max_clicks:
            giveaway.status = GiveawayStatus.FINISHED
            await giveaway.save(update_fields=["status"])

    return giveaway, click


async def finish_giveaway(giveaway_id: UUID) -> list[GiveawayClick]:
    """Distribute diamonds harmonically among all clickers. Returns paid clicks."""
    async with in_transaction():
        giveaway = await Giveaway.select_for_update().get(id=giveaway_id)
        if giveaway.status == GiveawayStatus.CANCELLED:
            return []

        clicks = await GiveawayClick.filter(giveaway_id=giveaway_id).order_by("click_order").all()

        if not clicks:
            # Refund sender
            sender_locked = await User.select_for_update().get(id=giveaway.sender_id)
            sender_locked.diamonds += giveaway.total_diamonds
            await sender_locked.save(update_fields=["diamonds"])
            await Transaction.create(
                user=sender_locked,
                type=TransactionType.GIVEAWAY_PAYOUT,
                diamonds_amount=giveaway.total_diamonds,
                related_giveaway_id=giveaway.id,
                status=TransactionStatus.REFUNDED,
                note="No clicks — refund",
            )
            giveaway.status = GiveawayStatus.FINISHED
            await giveaway.save(update_fields=["status"])
            return []

        # Harmonic distribution
        weights = [1.0 / (i + 1) for i in range(len(clicks))]
        total_weight = sum(weights)
        shares = [w / total_weight for w in weights]

        # Discrete diamonds
        amounts = [math.floor(giveaway.total_diamonds * s) for s in shares]
        leftover = giveaway.total_diamonds - sum(amounts)
        # Distribute leftover to first clickers
        i = 0
        while leftover > 0:
            amounts[i % len(amounts)] += 1
            leftover -= 1
            i += 1

        for click, amount in zip(clicks, amounts, strict=False):
            click.diamonds_received = amount
            await click.save(update_fields=["diamonds_received"])

            user_locked = await User.select_for_update().get(id=click.user_id)
            user_locked.diamonds += amount
            await user_locked.save(update_fields=["diamonds"])

            await Transaction.create(
                user=user_locked,
                type=TransactionType.GIVEAWAY_PAYOUT,
                diamonds_amount=amount,
                related_giveaway_id=giveaway.id,
                status=TransactionStatus.COMPLETED,
                note=f"Click order {click.click_order}",
            )

        giveaway.status = GiveawayStatus.FINISHED
        await giveaway.save(update_fields=["status"])

    logger.info(f"Giveaway {giveaway_id} finished: {len(clicks)} clicks paid out")
    return clicks


# === 3. Game bounty (escrow + payout) ===


async def escrow_bounty(initiator: User, amount_per_winner: int) -> int:
    """Reserve 10x bounty from initiator. Returns total pool."""
    pool = amount_per_winner * 10
    async with in_transaction():
        user_locked = await User.select_for_update().get(id=initiator.id)
        if user_locked.diamonds < pool:
            raise GiveawayError("game-bounty-insufficient")
        user_locked.diamonds -= pool
        await user_locked.save(update_fields=["diamonds"])
        await Transaction.create(
            user=user_locked,
            type=TransactionType.GAME_BOUNTY_ESCROW,
            diamonds_amount=-pool,
            status=TransactionStatus.COMPLETED,
        )
    return pool


async def payout_bounty(
    pool: int,
    per_winner: int,
    winner_user_ids: list[int],
    initiator_id: int | None,
    game_id: UUID,
) -> None:
    """Distribute bounty pool among winners; refund leftover to initiator."""
    if not winner_user_ids:
        # Refund all
        if initiator_id is not None:
            async with in_transaction():
                ulock = await User.select_for_update().get(id=initiator_id)
                ulock.diamonds += pool
                await ulock.save(update_fields=["diamonds"])
                await Transaction.create(
                    user=ulock,
                    type=TransactionType.GAME_BOUNTY_REFUND,
                    diamonds_amount=pool,
                    related_game_id=game_id,
                    status=TransactionStatus.COMPLETED,
                )
        return

    if len(winner_user_ids) <= 10:
        per = per_winner
        leftover = pool - per * len(winner_user_ids)
    else:
        per = pool // len(winner_user_ids)
        leftover = pool - per * len(winner_user_ids)

    async with in_transaction():
        for uid in winner_user_ids:
            ulock = await User.select_for_update().get(id=uid)
            ulock.diamonds += per
            await ulock.save(update_fields=["diamonds"])
            await Transaction.create(
                user=ulock,
                type=TransactionType.GAME_BOUNTY_PAYOUT,
                diamonds_amount=per,
                related_game_id=game_id,
                status=TransactionStatus.COMPLETED,
            )

        if leftover > 0 and initiator_id is not None:
            ulock = await User.select_for_update().get(id=initiator_id)
            ulock.diamonds += leftover
            await ulock.save(update_fields=["diamonds"])
            await Transaction.create(
                user=ulock,
                type=TransactionType.GAME_BOUNTY_REFUND,
                diamonds_amount=leftover,
                related_game_id=game_id,
                status=TransactionStatus.COMPLETED,
                note="Bounty leftover",
            )
