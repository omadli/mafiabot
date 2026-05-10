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

                # Sleep until phase ends
                if state.phase_ends_at is not None:
                    delay = state.phase_ends_at - int(time.time())
                    if delay > 0:
                        await asyncio.sleep(delay)

                # Reload state (may have changed)
                state = await load_state(group_id)
                if state is None or state.phase in (Phase.FINISHED, Phase.CANCELLED):
                    break

                # Transition
                await cls._advance_phase(bot, state)
                await save_state(state)

                if on_phase_change is not None:
                    try:
                        await on_phase_change(state)
                    except Exception as e:
                        logger.exception(f"on_phase_change failed: {e}")

                # Emit WS event to admin subscribers
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

                # Check winner
                if state.phase != Phase.WAITING:
                    winner = check_winner(state)
                    if winner is not None:
                        state.winner_team = winner
                        state.winner_user_ids = winner_user_ids(state, winner)
                        await save_state(state)
                        await finish_game(state, winner)
                        if on_phase_change is not None:
                            await on_phase_change(state)
                        break

        except asyncio.CancelledError:
            logger.info(f"Phase loop cancelled for group {group_id}")
            raise
        except Exception as e:
            logger.exception(f"Phase loop error for group {group_id}: {e}")
        finally:
            cls._tasks.pop(group_id, None)

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
            state.current_round().__dict__["pending_hang_target"] = leader_id
            state.phase = Phase.HANGING_CONFIRM
            state.phase_ends_at = int(time.time()) + timings.get("hanging_confirm", 15)
            return

        if state.phase == Phase.HANGING_CONFIRM:
            # Tally yes/no, execute or skip
            await cls._tally_hanging_confirm(state)

            # If Kamikaze was hanged → trigger choice prompt
            kamikaze_id = state.current_round().__dict__.get("kamikaze_pending_choice")
            if kamikaze_id:
                from app.bot.handlers.private.special_actions import send_kamikaze_choice

                await send_kamikaze_choice(bot, state, kamikaze_id)

            state.round_num += 1
            state.phase = Phase.NIGHT
            state.phase_ends_at = int(time.time()) + timings.get("night", 60)
            return

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

        confirm_data = state.current_round().__dict__.get("hanging_confirm", {})
        target_id = state.current_round().__dict__.get("pending_hang_target")
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
        state.current_round().__dict__["hang_yes_total"] = yes_total
        state.current_round().__dict__["hang_no_total"] = no_total

        # If no confirmation votes at all — auto-confirm (fall through)
        if not confirm_data or (yes_total == 0 and no_total == 0):
            yes_total = 1  # default "yes"

        if no_total >= yes_total:
            # Cancelled
            logger.info(f"Hanging cancelled by 👎 (yes={yes_total}, no={no_total})")
            state.current_round().__dict__["hang_cancelled"] = True
            state.current_round().hanged = None
            state.current_votes = {}
            return

        # Vote shield
        if "vote_shield" in target.items_active:
            target.items_active.remove("vote_shield")
            logger.info(f"Player {target_id} saved by vote_shield")
            state.current_round().hanged = None
            state.current_votes = {}
            return

        # Lawyer hanging protection
        lawyer_protected: list[int] = state.current_round().__dict__.get("lawyer_protected", [])
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
        state.current_round().__dict__["hanged_role"] = target.role
        state.current_round().__dict__["hanged_name"] = target.first_name

        if target.role == "kamikaze":
            state.current_round().__dict__["kamikaze_pending_choice"] = target.user_id

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
            target.items_active.remove("vote_shield")
            logger.info(f"Player {target_id} saved by vote_shield")
            state.current_round().hanged = None
            state.current_votes = {}
            return

        # Lawyer hanging protection (set during night)
        lawyer_protected: list[int] = state.current_round().__dict__.get("lawyer_protected", [])
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
            state.extra = state.extra if hasattr(state, "extra") else {}
            # We'll check this in win conditions

        # Kamikaze: if hanged, choose 1 to take
        if target.role == "kamikaze":
            # Schedule a prompt — handled by hook/messaging
            state.current_round().__dict__["kamikaze_pending_choice"] = target.user_id

        # Arsonist hanged: chain not triggered (he can only trigger via final_night button at night)
        logger.info(f"Player {target_id} voted out (role={target.role})")
        state.current_votes = {}
