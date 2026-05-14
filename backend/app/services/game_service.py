"""Game lifecycle service — create, register, start, finish.

Stateless module functions. Uses Redis (or memory) for live state,
DB only on game finish (Game.history JSON + GameResult rows).
"""

from __future__ import annotations

import time
from datetime import UTC
from uuid import UUID

from loguru import logger

from app.core.distribution import distribute_mvp_roles
from app.core.redis_state import get_state_backend
from app.core.roles import get_role
from app.core.state import (
    GameState,
    Phase,
    PlayerState,
    Team,
    game_state_key,
)
from app.db.models import Game, GameStatus, Group, User, WinnerTeam


class GameError(Exception):
    """Domain error from game service (i18n key as message)."""


# === State persistence ===


async def load_state(group_id: int) -> GameState | None:
    backend = get_state_backend()
    raw = await backend.get(game_state_key(group_id))
    if raw is None:
        return None
    return GameState.from_redis(raw)


async def save_state(state: GameState) -> None:
    backend = get_state_backend()
    await backend.set(game_state_key(state.group_id), state.to_redis())


async def delete_state(group_id: int) -> None:
    backend = get_state_backend()
    await backend.delete(game_state_key(group_id))


# === User active game tracking ===


async def get_user_active_game_id(user_id: int) -> UUID | None:
    user = await User.get_or_none(id=user_id)
    if user is None or user.active_game_id is None:
        return None
    return user.active_game_id


async def set_user_active_game(user_id: int, game_id: UUID | None) -> None:
    user = await User.get_or_none(id=user_id)
    if user is None:
        return
    user.active_game_id = game_id
    await user.save(update_fields=["active_game_id"])


# === Game creation ===


async def create_game(
    group: Group, host_user: User, bounty_per_winner: int | None = None
) -> GameState:
    """Create a new game in WAITING phase."""
    if not group.onboarding_completed:
        raise GameError("game-onboarding-required")

    existing = await load_state(group.id)
    if existing is not None and existing.phase != Phase.FINISHED:
        raise GameError("game-already-running")

    await group.fetch_related("settings")
    settings = group.settings

    state = GameState(
        group_id=group.id,
        chat_id=group.id,
        phase=Phase.WAITING,
        settings=_settings_snapshot(settings),
        bounty_per_winner=bounty_per_winner,
        bounty_pool=bounty_per_winner * 10 if bounty_per_winner else None,
        bounty_initiator_id=host_user.id if bounty_per_winner else None,
        creator_user_id=host_user.id,
    )

    # Set phase end time (registration timeout)
    reg_secs = settings.timings.get("registration", 120) if settings else 120
    state.phase_ends_at = int(time.time()) + reg_secs

    await save_state(state)
    logger.info(f"Game created in group {group.id} by user {host_user.id}")
    return state


def _settings_snapshot(settings: object) -> dict:
    """Extract settings JSON for game snapshot."""
    if settings is None:
        return {}
    return {
        "language": getattr(settings, "language", "uz"),
        "timings": getattr(settings, "timings", {}),
        "silence": getattr(settings, "silence", {}),
        "items_allowed": getattr(settings, "items_allowed", {}),
        "permissions": getattr(settings, "permissions", {}),
        "gameplay": getattr(settings, "gameplay", {}),
        "display": getattr(settings, "display", {}),
        "afk": getattr(settings, "afk", {}),
        "messages": getattr(settings, "messages", {}),
        "roles": getattr(settings, "roles", {}),
    }


# === Player registration ===


async def register_player(state: GameState, user: User) -> PlayerState:
    """Add user to game (registration phase)."""
    if state.phase != Phase.WAITING:
        raise GameError("join-no-active-registration")

    # Check if already in this game
    if state.get_player(user.id) is not None:
        raise GameError("join-already-in-this-game")

    max_players = state.settings.get("gameplay", {}).get("max_players", 30)
    if len(state.players) >= max_players:
        raise GameError("join-game-full")

    join_order = len(state.players) + 1
    player = PlayerState(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        join_order=join_order,
        role="citizen",  # placeholder — assigned at game start
        team=Team.CITIZENS,
    )
    state.players.append(player)
    await save_state(state)
    await set_user_active_game(user.id, state.id)
    logger.info(f"Player {user.id} joined game {state.id} (order={join_order})")
    return player


async def unregister_player(state: GameState, user_id: int) -> bool:
    """Remove player from registration (only WAITING phase)."""
    if state.phase != Phase.WAITING:
        return False
    state.players = [p for p in state.players if p.user_id != user_id]
    # Reorder
    for idx, p in enumerate(state.players, start=1):
        p.join_order = idx
    await save_state(state)
    await set_user_active_game(user_id, None)
    logger.info(f"Player {user_id} unregistered from game {state.id}")
    return True


# === Game start ===


async def start_game(state: GameState) -> GameState:
    """Transition WAITING → NIGHT (round 1). Assign roles."""
    if state.phase != Phase.WAITING:
        raise GameError("game-cannot-start-not-waiting")

    min_players = state.settings.get("gameplay", {}).get("min_players", 4)
    if len(state.players) < min_players:
        raise GameError("game-not-enough-players")

    # Assign roles
    user_ids = [p.user_id for p in state.players]
    mafia_ratio = state.settings.get("gameplay", {}).get("mafia_ratio", "low")
    enabled = state.settings.get("roles", {})
    assignments = distribute_mvp_roles(user_ids, mafia_ratio=mafia_ratio, enabled_roles=enabled)

    role_map = {a.user_id: a.role for a in assignments}
    for p in state.players:
        p.role = role_map[p.user_id]
        role_obj = get_role(p.role)
        p.team = role_obj.team

    # Honor 🃏 special_role picks. For each player who pre-paid a
    # special_role credit and picked a specific role, swap their assigned
    # role with whichever player got that role in random distribution.
    # If the picked role isn't in THIS game's distribution, the credit is
    # NOT consumed — the pick carries over to a future game.
    await _apply_special_role_picks(state)

    # Activate items from inventory (settings.enabled + items_allowed in group)
    items_allowed = state.settings.get("items_allowed", {})
    for p in state.players:
        p.items_active = await _resolve_active_items(p.user_id, items_allowed)

    # Persist Game record (status=running) in DB
    await Game.create(
        id=state.id,
        group_id=state.group_id,
        status=GameStatus.RUNNING,
        bounty_per_winner=state.bounty_per_winner,
        bounty_pool=state.bounty_pool,
        bounty_initiator_id=state.bounty_initiator_id,
        settings_snapshot=state.settings,
        history={},
    )
    state.started_at = int(time.time())

    # Move to night #1
    state.phase = Phase.NIGHT
    state.round_num = 1
    night_secs = state.settings.get("timings", {}).get("night", 60)
    state.phase_ends_at = int(time.time()) + night_secs

    await save_state(state)
    logger.info(f"Game {state.id} started with {len(state.players)} players")
    return state


# === Game finish ===


async def finish_game(state: GameState, winner: Team | None) -> None:
    """Persist final state to DB, run stats finalization, clean up Redis."""
    from datetime import datetime

    state.phase = Phase.FINISHED
    state.winner_team = winner
    state.finished_at = int(time.time())

    if winner is not None and not state.winner_user_ids:
        # Phase manager normally fills winner_user_ids via winner_user_ids().
        # Fallback only fires when finish_game is called directly (rare):
        # team wins → alive members only, dead are not winners.
        from app.core.win_conditions import winner_user_ids as _wuids

        state.winner_user_ids = _wuids(state, winner)

    # Persist to DB
    db_game = await Game.get_or_none(id=state.id)
    if db_game is not None:
        db_game.status = GameStatus.FINISHED
        db_game.finished_at = datetime.now(UTC)
        db_game.winner_team = (
            WinnerTeam(winner.value) if winner is not None else None  # type: ignore[arg-type]
        )
        db_game.history = state.to_history_dict()
        await db_game.save()

    # Run stats finalization (GameResult, UserStats, GroupUserStats, ELO)
    try:
        from app.services.stats_service import finalize_game_stats

        await finalize_game_stats(state)
    except Exception as e:
        logger.exception(f"Stats finalization failed for game {state.id}: {e}")

    # Per-player game-end DM (role, won/lost, XP/ELO/$). Best-effort —
    # any failure here MUST NOT block bounty payout or state cleanup.
    try:
        from app.main import bot
        from app.services.game_end_dm import send_per_player_game_end_dm

        if bot is not None:
            await send_per_player_game_end_dm(bot, state)
    except Exception as e:
        logger.exception(f"Game-end DM dispatch failed for game {state.id}: {e}")

    # Bounty payout (if /game N was used)
    if state.bounty_pool and state.bounty_per_winner and state.winner_user_ids:
        try:
            from app.services.giveaway_service import payout_bounty

            await payout_bounty(
                pool=state.bounty_pool,
                per_winner=state.bounty_per_winner,
                winner_user_ids=state.winner_user_ids,
                initiator_id=state.bounty_initiator_id,
                game_id=state.id,
            )
        except Exception as e:
            logger.exception(f"Bounty payout failed for game {state.id}: {e}")

    # Clear active_game for all participants
    for p in state.players:
        await set_user_active_game(p.user_id, None)

    # Remove Redis state
    await delete_state(state.group_id)

    logger.info(
        f"Game {state.id} finished, winner={winner}, "
        f"duration={state.finished_at - (state.started_at or state.finished_at)}s"
    )


async def _apply_special_role_picks(state: GameState) -> None:
    """Swap roles for players who pre-paid a 🃏 special_role pick.

    Runs AFTER distribute_mvp_roles. For each picker:
      * If they already lucked into their picked role, just consume the
        credit silently.
      * Otherwise swap with whichever player got the picked role.
      * If the picked role isn't in this game's distribution at all, do
        nothing (the credit stays so the pick carries to a future game).
    """
    from app.db.models import UserInventory

    for player in state.players:
        inv = await UserInventory.get_or_none(user_id=player.user_id)
        if inv is None:
            continue
        sr_settings = (inv.settings or {}).get("special_role", {})
        forced_role = sr_settings.get("next_role")
        if not forced_role:
            continue

        if player.role == forced_role:
            await _consume_special_role_credit(player.user_id, inv)
            continue

        other = next(
            (p for p in state.players if p.role == forced_role and p.user_id != player.user_id),
            None,
        )
        if other is None:
            # Role missing from this distribution — keep the credit for
            # the next game.
            continue

        player.role, other.role = forced_role, player.role
        player.team = get_role(player.role).team
        other.team = get_role(other.role).team
        logger.info(
            f"special_role swap: user {player.user_id} forced into {forced_role} "
            f"(swapped with user {other.user_id})"
        )
        await _consume_special_role_credit(player.user_id, inv)


async def _consume_special_role_credit(user_id: int, inv: object) -> None:
    """Decrement special_role inventory + clear the picked role."""
    from app.db.models import UserInventory

    new_settings = dict(getattr(inv, "settings", None) or {})
    sr = dict(new_settings.get("special_role", {}))
    sr.pop("next_role", None)
    sr["enabled"] = False
    new_settings["special_role"] = sr
    new_count = max(0, getattr(inv, "special_role", 0) - 1)
    await UserInventory.filter(user_id=user_id).update(
        special_role=new_count, settings=new_settings
    )


async def _resolve_active_items(user_id: int, items_allowed: dict) -> list[str]:
    """Determine which items the user has + activated + group allows.

    Decrements inventory counters for items that go into the game (one-shot consumables).
    """
    from app.db.models import UserInventory

    inv = await UserInventory.get_or_none(user_id=user_id)
    if inv is None:
        return []

    settings = inv.settings or {}
    active: list[str] = []

    item_fields = [
        "shield",
        "killer_shield",
        "vote_shield",
        "rifle",
        "mask",
        "fake_document",
    ]

    decremented: dict[str, int] = {}
    for field in item_fields:
        # Group must allow it
        if not items_allowed.get(field, True):
            continue
        # User has at least 1
        qty = getattr(inv, field, 0)
        if qty <= 0:
            continue
        # User enabled it in settings
        item_settings = settings.get(field, {})
        if not item_settings.get("enabled", False):
            continue
        # Activate + decrement
        active.append(field)
        new_qty = qty - 1
        setattr(inv, field, new_qty)
        decremented[field] = new_qty

    if decremented:
        # Workaround: UserInventory.user is OneToOneField(pk=True), so
        # `inv.save()` hits the same Tortoise 0.21 bug as GroupSettings.
        # Use filter().update() with explicit column kwargs.
        await UserInventory.filter(user_id=user_id).update(**decremented)

    return active


async def cancel_game(state: GameState, reason: str = "cancelled") -> None:
    """Cancel game (admin /stop or auto). Refund bounty if applicable."""
    from datetime import datetime

    state.phase = Phase.CANCELLED
    state.finished_at = int(time.time())

    db_game = await Game.get_or_none(id=state.id)
    if db_game is not None:
        db_game.status = GameStatus.CANCELLED
        db_game.finished_at = datetime.now(UTC)
        db_game.history = state.to_history_dict()
        await db_game.save()

    # Refund bounty escrow
    if state.bounty_pool and state.bounty_initiator_id:
        try:
            from app.services.giveaway_service import payout_bounty

            await payout_bounty(
                pool=state.bounty_pool,
                per_winner=0,
                winner_user_ids=[],  # empty → full refund
                initiator_id=state.bounty_initiator_id,
                game_id=state.id,
            )
        except Exception as e:
            logger.exception(f"Bounty refund failed for game {state.id}: {e}")

    for p in state.players:
        await set_user_active_game(p.user_id, None)

    await delete_state(state.group_id)
    logger.info(f"Game {state.id} cancelled: {reason}")
