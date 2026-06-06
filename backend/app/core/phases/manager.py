"""Phase manager — orchestrates game phase transitions with asyncio timers.

Each game has a single asyncio task (PhaseManager) that:
  1. Sleeps until phase_ends_at
  2. Triggers phase transition (with hooks for early end)
  3. Loops until game finished
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import ClassVar

from aiogram import Bot
from loguru import logger

from app.core.actions import ActionResolver
from app.core.state import GameState, Phase
from app.core.win_conditions import check_winner, winner_user_ids
from app.services.game_service import (
    finish_game,
    load_state,
    save_state,
)


class PhaseManager:
    """Owns the timer loop for a single game."""

    # group_id → task (so we can cancel on /stop)
    _tasks: ClassVar[dict[int, asyncio.Task]] = {}
    # group_id → lock that serializes tick_once. The timer loop and any
    # external force-advance (e.g. /leave by the hang target) must not
    # interleave a single phase transition, otherwise night actions get
    # re-resolved or the round counter bumps twice.
    _locks: ClassVar[dict[int, asyncio.Lock]] = {}

    @classmethod
    def _lock_for(cls, group_id: int) -> asyncio.Lock:
        lock = cls._locks.get(group_id)
        if lock is None:
            lock = asyncio.Lock()
            cls._locks[group_id] = lock
        return lock

    @classmethod
    def start_for(
        cls,
        bot: Bot,
        group_id: int,
        on_phase_change: Callable[[GameState], Awaitable[None]] | None = None,
    ) -> None:
        """Start (or restart) phase loop for a game."""
        if group_id in cls._tasks and not cls._tasks[group_id].done():
            logger.debug(f"Phase manager already running for group {group_id}")
            return

        task = asyncio.create_task(cls._loop(bot, group_id, on_phase_change))
        cls._tasks[group_id] = task
        logger.info(f"Phase manager started for group {group_id}")

    @classmethod
    def cancel_for(cls, group_id: int) -> None:
        task = cls._tasks.pop(group_id, None)
        if task is not None and not task.done():
            task.cancel()
            logger.info(f"Phase manager cancelled for group {group_id}")
        # Drop the lock — the next game in this group gets a fresh one.
        cls._locks.pop(group_id, None)

    @classmethod
    async def _loop(
        cls,
        bot: Bot,
        group_id: int,
        on_phase_change: Callable[[GameState], Awaitable[None]] | None,
    ) -> None:
        try:
            while True:
                state = await load_state(group_id)
                if state is None or state.phase in (Phase.FINISHED, Phase.CANCELLED):
                    break

                # Snapshot the phase we are sleeping for so we can detect
                # an external transition (e.g. admin /start moved WAITING →
                # NIGHT while we were asleep on the OLD registration deadline).
                sleep_phase = state.phase
                sleep_deadline = state.phase_ends_at

                # Sleep until phase ends.
                # phase_ends_at = None → indefinite registration (after /extend).
                # We still wake periodically to allow external trigger via
                # state changes (e.g. /start by admin sets phase to NIGHT).
                if sleep_deadline is not None:
                    delay = sleep_deadline - int(time.time())
                    if delay > 0:
                        await asyncio.sleep(delay)
                else:
                    # Sleep in 5s chunks and re-read state each cycle.
                    # An external /start handler can transition WAITING → NIGHT
                    # directly; this loop will detect the new phase and resume.
                    await asyncio.sleep(5)
                    state = await load_state(group_id)
                    if state is None or state.phase != Phase.WAITING:
                        continue  # phase changed externally — re-enter loop
                    # Still in WAITING with no deadline → keep waiting silently
                    continue

                # Reload state (may have changed)
                state = await load_state(group_id)
                if state is None or state.phase in (Phase.FINISHED, Phase.CANCELLED):
                    break

                # Detect mid-sleep external transition: phase changed under us
                # (e.g. admin /start → start_game() flipped WAITING → NIGHT and
                # reset phase_ends_at to a future time). If the new phase still
                # has time remaining, do NOT advance — loop and sleep again on
                # the fresh deadline. Without this guard, the manager wakes at
                # the OLD deadline and immediately fires NIGHT → DAY, robbing
                # players of their night-action window.
                if (
                    state.phase != sleep_phase
                    and state.phase_ends_at is not None
                    and state.phase_ends_at - int(time.time()) > 0
                ):
                    continue

                new_phase = await cls.tick_once(bot, group_id, on_phase_change, force=True)
                # tick_once returns None only when the state vanished or was
                # already terminal — in either case the loop is done.
                if new_phase is None or new_phase in (Phase.CANCELLED, Phase.FINISHED):
                    break

        except asyncio.CancelledError:
            logger.info(f"Phase loop cancelled for group {group_id}")
            raise
        except Exception as e:
            logger.exception(f"Phase loop error for group {group_id}: {e}")
        finally:
            cls._tasks.pop(group_id, None)

    @classmethod
    async def tick_once(
        cls,
        bot: Bot,
        group_id: int,
        on_phase_change: Callable[[GameState], Awaitable[None]] | None = None,
        *,
        force: bool = False,
    ) -> Phase | None:
        """Run exactly one phase advance + post-advance bookkeeping.

        Returns the new `state.phase` after the advance, or `None` when
        the game state is missing or already terminal so the caller can
        bail out.

        Two callers:
          - `_loop` (timer-driven): calls with `force=True` after its own
            deadline + external-transition checks have already cleared.
          - `sandbox_service.advance_phase` (manual mode): calls directly
            on operator click. Same `force=True`.

        Both behaviours are identical from here on — winner detection,
        state save, on_phase_change hook, and the `phase_change` WS
        event match the original loop body verbatim.

        Serialized on a per-group lock so the timer loop and external
        callers (e.g. /leave by the hang target forcing an early
        advance) cannot interleave a single phase transition.
        """
        async with cls._lock_for(group_id):
            state = await load_state(group_id)
            if state is None or state.phase in (Phase.FINISHED, Phase.CANCELLED):
                return None

            # Advance the phase. `_advance_phase` may itself terminate the game
            # (insufficient players at end of registration, etc.).
            await cls._advance_phase(bot, state)
            # _advance_phase may have ended the game (cancel_game / finish_game
            # already wiped the Redis state). Re-saving here would resurrect a
            # CANCELLED/FINISHED state in Redis and block the next /game.
            if state.phase not in (Phase.CANCELLED, Phase.FINISHED):
                await save_state(state)

            # === Winner check BEFORE the next-phase intro ===
            # If the phase that just completed produced a game-ending event
            # (night kills wiped a team, or a critical hanging finished
            # mafia/citizens), we must end the game right here — not after
            # the next NIGHT/DAY has already been announced to the group.
            # The on_phase_change(FINISHED) handler narrates the killing
            # event and then the game-over message.
            if state.phase not in (Phase.WAITING, Phase.CANCELLED, Phase.FINISHED):
                winner = check_winner(state)
                if winner is not None:
                    state.winner_team = winner
                    state.winner_user_ids = winner_user_ids(state, winner)
                    state.phase = Phase.FINISHED
                    await save_state(state)
                    await finish_game(state, winner)
                    await cls._invoke_hook(state, on_phase_change)
                    await cls._emit_phase_change(state)
                    return state.phase

            await cls._invoke_hook(state, on_phase_change)
            await cls._emit_phase_change(state)
            return state.phase

    @staticmethod
    async def _invoke_hook(
        state: GameState,
        on_phase_change: Callable[[GameState], Awaitable[None]] | None,
    ) -> None:
        if on_phase_change is None:
            return
        try:
            await on_phase_change(state)
        except Exception as e:
            logger.exception(f"on_phase_change failed: {e}")

    @staticmethod
    async def _emit_phase_change(state: GameState) -> None:
        try:
            from app.services.ws_broker import emit_game_event

            await emit_game_event(
                "phase_change",
                game_id=str(state.id),
                group_id=state.group_id,
                phase=state.phase.value,
                round_num=state.round_num,
                alive=len(state.alive_players()),
            )
        except Exception as e:
            logger.debug(f"WS emit failed: {e}")

    @classmethod
    async def _advance_phase(cls, bot: Bot, state: GameState) -> None:
        """Move to next phase (mutates state in-place)."""
        timings = state.settings.get("timings", {})

        if state.phase == Phase.WAITING:
            # Auto-start if enough players, else cancel
            min_players = state.settings.get("gameplay", {}).get("min_players", 4)
            if len(state.players) >= min_players:
                from app.services.game_service import start_game

                await start_game(state)
                # start_game already advanced state to NIGHT
                return
            # Not enough players — cancel
            from app.services.game_service import cancel_game

            await cancel_game(state, reason="not-enough-players")
            return

        if state.phase == Phase.NIGHT:
            # AFK tracker BEFORE actions cleared
            from app.services.afk_service import track_phase_inactivity

            await track_phase_inactivity(bot, state, Phase.NIGHT)

            # Resolve actions
            resolver = ActionResolver()
            outcome = resolver.resolve(state)
            state.current_round().night_deaths = outcome.deaths

            # Burn rifle inventory for shots that actually had to pierce
            # something. The resolver collects user_ids in `rifles_consumed`;
            # a "Ha, ot" against an undefended target is NOT in this list,
            # so the rifle slot survives. Deduped because two rifle shots
            # by the same actor (theoretically impossible — one target per
            # actor — but defensive) shouldn't double-debit.
            if outcome.rifles_consumed:
                from app.db.models import UserInventory

                for uid in set(outcome.rifles_consumed):
                    inv = await UserInventory.get_or_none(user_id=uid)
                    if inv is None or inv.rifle < 1:
                        continue
                    await UserInventory.filter(user_id=uid).update(rifle=max(0, inv.rifle - 1))

            # Burn one DB inventory slot per shield that actually came off
            # `items_active` this night — i.e. the player wasn't premium,
            # or their premium bonus charge had already been spent. The
            # resolver only appends here when the *final* slot was used;
            # bonus charges leave the entry off this list so the stock is
            # preserved exactly like the in-memory items_active is.
            if outcome.inventory_consumed:
                from app.db.models import UserInventory

                # Aggregate same-user/same-item entries (e.g. theoretical
                # multi-attacker shield burns) into a single per-pair
                # decrement so we don't emit N updates for one round.
                tally: dict[tuple[int, str], int] = {}
                for uid, item in outcome.inventory_consumed:
                    tally[(uid, item)] = tally.get((uid, item), 0) + 1
                for (uid, item), n in tally.items():
                    inv = await UserInventory.get_or_none(user_id=uid)
                    if inv is None:
                        continue
                    cur = getattr(inv, item, 0)
                    if cur < 1:
                        continue
                    await UserInventory.filter(user_id=uid).update(**{item: max(0, cur - n)})

            # Send role feedback DMs (Detective check result, Doctor visitors, Hooker)
            from app.services.role_feedback import send_role_feedback

            await send_role_feedback(bot, state, outcome)

            # Mage reactive prompts
            if outcome.pending_mage_reactions:
                from app.bot.handlers.private.special_actions import (
                    send_mage_reaction_prompt,
                )

                locale = state.settings.get("language", "uz")
                for mage_react in outcome.pending_mage_reactions:
                    await send_mage_reaction_prompt(
                        bot,
                        mage_react.actor_id,
                        mage_react.attacker_role,
                        mage_react.attacker_id,
                        locale,
                    )

            # Move to day
            state.phase = Phase.DAY
            state.phase_ends_at = int(time.time()) + timings.get("day", 45)
            return

        if state.phase == Phase.DAY:
            state.phase = Phase.VOTING
            state.phase_ends_at = int(time.time()) + timings.get("hanging_vote", 25)
            return

        if state.phase == Phase.VOTING:
            # AFK tracker for voting
            from app.services.afk_service import track_phase_inactivity

            await track_phase_inactivity(bot, state, Phase.VOTING)

            # Persist this round's day votes into the round log BEFORE the
            # resolution paths below clear `current_votes`. Without this the
            # stored Game.history (and vote-based stats) would always show
            # empty votes. Snapshot copy — does not disturb the tally that
            # `_find_vote_leader` reads next.
            state.current_round().day_votes = list(state.current_votes.values())

            # Find leader (most votes)
            leader_id = cls._find_vote_leader(state)
            if leader_id is None or leader_id == 0:
                # Skip / no consensus → straight to next night
                state.current_round().hanged = None
                state.current_votes = {}
                state.round_num += 1
                state.phase = Phase.NIGHT
                state.phase_ends_at = int(time.time()) + timings.get("night", 60)
                return

            # Move to HANGING_CONFIRM phase (👍/👎)
            state.current_round().extra["pending_hang_target"] = leader_id
            state.phase = Phase.HANGING_CONFIRM
            state.phase_ends_at = int(time.time()) + timings.get("hanging_confirm", 15)
            return

        if state.phase == Phase.HANGING_CONFIRM:
            # Tally yes/no, execute or skip
            await cls._tally_hanging_confirm(state)

            # If Kamikaze was hanged → trigger choice prompt
            kamikaze_id = state.current_round().extra.get("kamikaze_pending_choice")
            if kamikaze_id:
                from app.bot.handlers.private.special_actions import send_kamikaze_choice

                await send_kamikaze_choice(bot, state, kamikaze_id)

            state.round_num += 1
            state.phase = Phase.NIGHT
            state.phase_ends_at = int(time.time()) + timings.get("night", 60)
            return

    @classmethod
    async def _decrement_inventory_item(cls, user_id: int, item: str) -> None:
        """Debit a single inventory slot. Used by the vote-shield path
        when the SLOT was actually burned (not just a premium bonus).
        Mirrors the night-phase batch update in tick_once but for the
        single per-hanging case the day-phase only ever produces."""
        from app.db.models import UserInventory

        inv = await UserInventory.get_or_none(user_id=user_id)
        if inv is None:
            return
        cur = getattr(inv, item, 0)
        if cur < 1:
            return
        await UserInventory.filter(user_id=user_id).update(**{item: max(0, cur - 1)})

    @classmethod
    def _consume_vote_shield(cls, target) -> bool:  # type: ignore[no-untyped-def]
        """Same premium-bonus contract as ActionResolver._consume_shield —
        premium players get a second save off a single vote_shield slot
        before the item is finally stripped.

        Returns True when the final slot was burned so the caller can
        debit the DB inventory by 1; False when a premium-bonus charge
        absorbed the save and the slot is preserved.
        """
        item = "vote_shield"
        if not target.extra.get("is_premium"):
            if item in target.items_active:
                target.items_active.remove(item)
                return True
            return False
        uses_left: dict = target.extra.setdefault("shield_uses_left", {})
        remaining = uses_left.get(item, 1)
        if remaining > 0:
            uses_left[item] = remaining - 1
            return False
        if item in target.items_active:
            target.items_active.remove(item)
            return True
        return False

    @classmethod
    def _find_vote_leader(cls, state: GameState) -> int | None:
        """Find the user_id with most votes (Mayor 2x). None if no votes; 0 if "Hech kim" leads."""
        from app.core.roles import get_role

        if not state.current_votes:
            return None

        tally: dict[int, int] = {}
        for vote in state.current_votes.values():
            voter = state.get_player(vote.voter_id)
            weight = vote.weight
            if voter is not None:
                role = get_role(voter.role)
                weight = getattr(role, "vote_weight", 1)
            tally[vote.target_id] = tally.get(vote.target_id, 0) + weight

        if not tally:
            return None
        max_votes = max(tally.values())
        leaders = [uid for uid, v in tally.items() if v == max_votes]
        if len(leaders) > 1:
            return None  # tie → no hanging
        return leaders[0]

    @classmethod
    async def _tally_hanging_confirm(cls, state: GameState) -> None:
        """Process 👍/👎 votes. If yes > no → hang."""
        from app.core.state import DeathReason

        confirm_data = state.current_round().extra.get("hanging_confirm", {})
        target_id = state.current_round().extra.get("pending_hang_target")
        if not target_id:
            state.current_votes = {}
            return

        target = state.get_player(target_id)
        if target is None or not target.alive:
            state.current_votes = {}
            return

        yes_total = sum(confirm_data.get("yes", {}).values())
        no_total = sum(confirm_data.get("no", {}).values())

        # Persist totals for broadcast (👍 / 👎 breakdown reflects Mayor x2 weights)
        state.current_round().extra["hang_yes_total"] = yes_total
        state.current_round().extra["hang_no_total"] = no_total

        # Hang only on strict majority of 👍. A tie (including 0:0 — nobody
        # bothered to confirm) means the player survives.
        if yes_total <= no_total:
            logger.info(f"Hanging cancelled (yes={yes_total}, no={no_total})")
            state.current_round().extra["hang_cancelled"] = True
            state.current_round().hanged = None
            state.current_votes = {}
            return

        # Vote shield
        if "vote_shield" in target.items_active:
            slot_burned = cls._consume_vote_shield(target)
            if slot_burned:
                await cls._decrement_inventory_item(target.user_id, "vote_shield")
            # Flag the broadcast so _on_phase_change can announce
            # "{mention} osilishga qarshi himoyasidan foydalandi".
            state.current_round().extra["vote_shield_user"] = {
                "user_id": target.user_id,
                "name": target.first_name,
            }
            logger.info(f"Player {target_id} saved by vote_shield")
            state.current_round().hanged = None
            state.current_votes = {}
            return

        # Lawyer hanging protection
        lawyer_protected: list[int] = state.current_round().extra.get("lawyer_protected", [])
        if target_id in lawyer_protected:
            logger.info(f"Player {target_id} saved by Lawyer (hanging protection)")
            state.current_round().hanged = None
            state.current_votes = {}
            return

        # Death
        target.alive = False
        target.died_at_round = state.round_num
        target.died_at_phase = Phase.VOTING
        target.died_reason = DeathReason.VOTED_OUT
        state.current_round().hanged = target_id
        # Persist hanged role for broadcast (post-hang reveal)
        state.current_round().extra["hanged_role"] = target.role
        state.current_round().extra["hanged_name"] = target.first_name

        if target.role == "kamikaze":
            state.current_round().extra["kamikaze_pending_choice"] = target.user_id

        logger.info(f"Player {target_id} voted out (role={target.role})")
        state.current_votes = {}

    @classmethod
    async def _tally_votes(cls, state: GameState) -> None:
        """Count votes and execute hanging.

        - Mayor's vote weight = 2 (set at vote time, but we re-validate here).
        - Lawyer's "protect" target during night also gives hanging protection (1 use).
        - Vote shield item (vote_shield) saves from hanging.
        - Aferist proxy votes already use voter_id of impersonated user.
        """
        from app.core.roles import get_role
        from app.core.state import DeathReason

        if not state.current_votes:
            state.current_round().hanged = None
            return

        # Re-validate weights based on role (Mayor 2x)
        tally: dict[int, int] = {}
        for vote in state.current_votes.values():
            if vote.target_id == 0:
                continue
            voter = state.get_player(vote.voter_id)
            weight = vote.weight
            if voter is not None:
                role = get_role(voter.role)
                weight = getattr(role, "vote_weight", 1)
            tally[vote.target_id] = tally.get(vote.target_id, 0) + weight

        if not tally:
            state.current_round().hanged = None
            state.current_votes = {}
            return

        max_votes = max(tally.values())
        leaders = [uid for uid, v in tally.items() if v == max_votes]
        if len(leaders) > 1:
            state.current_round().hanged = None
            state.current_votes = {}
            return

        target_id = leaders[0]
        target = state.get_player(target_id)
        if target is None or not target.alive:
            state.current_votes = {}
            return

        # Vote shield (passive item)
        if "vote_shield" in target.items_active:
            slot_burned = cls._consume_vote_shield(target)
            if slot_burned:
                await cls._decrement_inventory_item(target.user_id, "vote_shield")
            state.current_round().extra["vote_shield_user"] = {
                "user_id": target.user_id,
                "name": target.first_name,
            }
            logger.info(f"Player {target_id} saved by vote_shield")
            state.current_round().hanged = None
            state.current_votes = {}
            return

        # Lawyer hanging protection (set during night)
        lawyer_protected: list[int] = state.current_round().extra.get("lawyer_protected", [])
        if target_id in lawyer_protected:
            logger.info(f"Player {target_id} saved by Lawyer (hanging protection)")
            state.current_round().hanged = None
            state.current_votes = {}
            return

        # Death (hanging)
        target.alive = False
        target.died_at_round = state.round_num
        target.died_at_phase = Phase.VOTING
        target.died_reason = DeathReason.VOTED_OUT
        state.current_round().hanged = target_id

        # Suicide special: if hanged, marks as winner via state.extra
        if target.role == "suicide":
            state.extra = state.extra if hasattr(state, "extra") else {}  # type: ignore[attr-defined,var-annotated,arg-type]
            # We'll check this in win conditions

        # Kamikaze: if hanged, choose 1 to take
        if target.role == "kamikaze":
            # Schedule a prompt — handled by hook/messaging
            state.current_round().extra["kamikaze_pending_choice"] = target.user_id

        # Arsonist hanged: chain not triggered (he can only trigger via final_night button at night)
        logger.info(f"Player {target_id} voted out (role={target.role})")
        state.current_votes = {}
