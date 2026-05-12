"""Action queue + resolver — 21 roles, items, transformations.

Resolution order (priority lower = first):
  10  hooker.sleep         (Don+kezuvchi: Don ustun)
  20  hobo.visit            (witness for kill detection)
  25  killer.kill           (Ninza — pierces shields)
  25  arsonist.queue        (target_queue)
  30  don.kill / mafia.kill / maniac.kill
  35  lawyer.protect        (komissar + osish himoyasi)
  40  doctor.heal
  50  detective.check / journalist.check
  55  snitch.target          (collusion check)
  60  crook.visit
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from loguru import logger

from app.core.state import (
    DeathReason,
    GameState,
    NightAction,
    Phase,
    PlayerState,
    Team,
)

# === Result types ===


@dataclass
class CheckResult:
    actor_id: int
    target_id: int
    target_name: str
    revealed_role: str
    revealed_team: Team
    by: str = "detective"  # detective | journalist


@dataclass
class HealResult:
    actor_id: int
    target_id: int
    target_name: str
    saved: bool
    visited_by_killers: list[str] = field(default_factory=list)


@dataclass
class HookerResult:
    actor_id: int
    target_id: int
    target_name: str


@dataclass
class HoboResult:
    """Daydi guvohlik natijasi."""

    actor_id: int
    target_id: int
    target_name: str
    target_died: bool
    killer_role: str | None
    blocked_by_mask: bool


@dataclass
class TransformResult:
    """Werewolf/Sergeant transformatsiya."""

    user_id: int
    new_role: str
    new_team: Team
    by_role: str


@dataclass
class MageReaction:
    """Sehrgar uchun pending reaksiya."""

    actor_id: int
    attacker_id: int
    attacker_role: str


@dataclass
class SnitchReveal:
    snitch_id: int
    target_id: int
    target_name: str
    revealed_role: str


@dataclass
class KamikazeTake:
    kamikaze_id: int
    victim_id: int
    by_hanging: bool


@dataclass
class NightOutcome:
    deaths: list[int] = field(default_factory=list)
    death_reasons: dict[int, DeathReason] = field(default_factory=dict)
    detective_results: list[CheckResult] = field(default_factory=list)
    journalist_results: list[CheckResult] = field(default_factory=list)
    doctor_results: list[HealResult] = field(default_factory=list)
    hooker_results: list[HookerResult] = field(default_factory=list)
    hobo_results: list[HoboResult] = field(default_factory=list)
    transformations: list[TransformResult] = field(default_factory=list)
    snitch_reveals: list[SnitchReveal] = field(default_factory=list)
    kamikaze_takes: list[KamikazeTake] = field(default_factory=list)
    pending_mage_reactions: list[MageReaction] = field(default_factory=list)
    sleeping: set[int] = field(default_factory=set)


# === Resolver ===


class ActionResolver:
    """Apply night actions in priority order and return outcome."""

    def resolve(self, state: GameState) -> NightOutcome:
        actions = list(state.current_actions.values())
        actions.sort(key=lambda a: self._priority(a))

        outcome = NightOutcome()

        # 1. Hooker sleeps
        sleeping_targets: set[int] = set()
        for a in actions:
            if a.action_type != "sleep" or a.target_id is None:
                continue
            if self._hooker_blocked_by_don(state, a):
                continue
            sleeping_targets.add(a.target_id)
            actor = state.get_player(a.actor_id)
            target = state.get_player(a.target_id)
            if actor and target:
                actor.extra["last_target"] = a.target_id
                outcome.hooker_results.append(
                    HookerResult(
                        actor_id=a.actor_id,
                        target_id=a.target_id,
                        target_name=target.first_name,
                    )
                )
        outcome.sleeping = sleeping_targets

        # 2. Filter out sleeping actors
        active_actions = [a for a in actions if a.actor_id not in sleeping_targets]

        # 3. Hobo visits
        hobo_visits: dict[int, int] = {}
        for a in active_actions:
            if a.action_type == "visit" and a.role == "hobo" and a.target_id is not None:
                hobo_visits[a.actor_id] = a.target_id

        # 4. Arsonist queue / final_night
        for a in active_actions:
            if a.role != "arsonist" or a.target_id is None:
                continue
            actor = state.get_player(a.actor_id)
            if actor is None:
                continue
            queue: list[int] = actor.extra.setdefault("target_queue", [])
            if a.action_type == "queue" and a.target_id not in queue:
                queue.append(a.target_id)
            elif a.action_type == "final_night":
                chain_targets = [*list(queue), actor.user_id]
                for tgt_id in chain_targets:
                    tgt = state.get_player(tgt_id)
                    if tgt is None or not tgt.alive:
                        continue
                    tgt.alive = False
                    tgt.died_at_round = state.round_num
                    tgt.died_at_phase = Phase.NIGHT
                    tgt.died_reason = DeathReason.KILLED_GAZABKOR
                    outcome.deaths.append(tgt_id)
                    outcome.death_reasons[tgt_id] = DeathReason.KILLED_GAZABKOR
                actor.extra["arsonist_triggered"] = True

        # 5. Lawyer protection
        lawyer_protected: set[int] = set()
        for a in active_actions:
            if (
                a.role == "lawyer"
                and a.target_id is not None
                and a.action_type in ("protect", "heal")
            ):
                lawyer_protected.add(a.target_id)
        state.current_round().__dict__["lawyer_protected"] = list(lawyer_protected)

        # 6. Build kill targets
        kill_targets: dict[int, list[tuple[str, int, NightAction]]] = {}
        for a in active_actions:
            if a.action_type == "kill" and a.target_id is not None:
                kill_targets.setdefault(a.target_id, []).append((a.role, a.actor_id, a))

        # 7. Heal targets
        heal_targets: dict[int, int] = {}
        for a in active_actions:
            if a.action_type == "heal" and a.role == "doctor" and a.target_id is not None:
                heal_targets[a.target_id] = a.actor_id
                if a.target_id == a.actor_id:
                    actor = state.get_player(a.actor_id)
                    if actor is not None:
                        actor.extra["self_heal_used"] = True

        # 8. Apply kills
        for target_id, attackers in kill_targets.items():
            target = state.get_player(target_id)
            if target is None or not target.alive:
                continue

            # Werewolf special handling
            if target.role == "werewolf":
                self._handle_werewolf_attack(state, target, attackers, outcome)
                continue

            # Mage reactive
            if target.role == "mage":
                for atk_role, atk_actor_id, _ in attackers:
                    outcome.pending_mage_reactions.append(
                        MageReaction(
                            actor_id=target.user_id,
                            attacker_id=atk_actor_id,
                            attacker_role=atk_role,
                        )
                    )
                target.extra.setdefault("pending_attacks", []).extend(
                    [(r, aid) for r, aid, _ in attackers]
                )
                continue

            # Lucky 50% save
            if target.role == "lucky" and random.random() < 0.5:
                logger.info(f"Lucky {target.user_id} survived (50% chance)")
                continue

            uses_rifle = any(act.used_item == "rifle" for _, _, act in attackers)
            piercing = uses_rifle or any(
                self._role_pierces_shields(role) for role, _, _ in attackers
            )

            saved_by_doctor = target_id in heal_targets and not piercing
            saved_by_killer_shield = (
                "killer_shield" in target.items_active
                and not uses_rifle
                and any(role == "killer" for role, _, _ in attackers)
            )
            saved_by_shield = "shield" in target.items_active and not piercing

            killer_role = attackers[0][0]
            if saved_by_doctor:
                outcome.doctor_results.append(
                    HealResult(
                        actor_id=heal_targets[target_id],
                        target_id=target_id,
                        target_name=target.first_name,
                        saved=True,
                        visited_by_killers=[r for r, _, _ in attackers],
                    )
                )
                continue
            if saved_by_killer_shield:
                target.items_active.remove("killer_shield")
                logger.debug(f"Player {target_id} saved by killer_shield")
                continue
            if saved_by_shield:
                target.items_active.remove("shield")
                logger.debug(f"Player {target_id} saved by shield")
                continue

            # Death
            target.alive = False
            target.died_at_round = state.round_num
            target.died_at_phase = Phase.NIGHT
            reason = self._death_reason_for_role(killer_role)
            target.died_reason = reason
            outcome.deaths.append(target_id)
            outcome.death_reasons[target_id] = reason
            logger.info(f"Player {target_id} died (killed by {killer_role})")

            # Kamikaze take-with-me
            if target.role == "kamikaze":
                killer_id = attackers[0][1]
                killer_player = state.get_player(killer_id)
                if killer_player is not None and killer_player.alive:
                    killer_player.alive = False
                    killer_player.died_at_round = state.round_num
                    killer_player.died_at_phase = Phase.NIGHT
                    killer_player.died_reason = DeathReason.KILLED_AFSUNGAR
                    outcome.deaths.append(killer_id)
                    outcome.death_reasons[killer_id] = DeathReason.KILLED_AFSUNGAR
                    outcome.kamikaze_takes.append(
                        KamikazeTake(kamikaze_id=target_id, victim_id=killer_id, by_hanging=False)
                    )

        # 9. Doctor visits without kill
        for target_id, doctor_id in heal_targets.items():
            if any(r.target_id == target_id for r in outcome.doctor_results):
                continue
            target = state.get_player(target_id)
            if target is None:
                continue
            outcome.doctor_results.append(
                HealResult(
                    actor_id=doctor_id,
                    target_id=target_id,
                    target_name=target.first_name,
                    saved=False,
                )
            )

        # 10. Detective check
        for a in active_actions:
            if a.action_type == "check" and a.role == "detective" and a.target_id is not None:
                target = state.get_player(a.target_id)
                actor = state.get_player(a.actor_id)
                if target is None or actor is None:
                    continue
                revealed = self._reveal_role_for_detective(target, lawyer_protected)
                outcome.detective_results.append(
                    CheckResult(
                        actor_id=actor.user_id,
                        target_id=target.user_id,
                        target_name=target.first_name,
                        revealed_role=revealed,
                        revealed_team=Team.CITIZENS if revealed == "citizen" else target.team,
                        by="detective",
                    )
                )
                actor.extra.setdefault("checks", []).append(target.user_id)
                # Remember revealed role so the next night's prompt can recap.
                # JSON keys must be strings (state is round-tripped via Redis).
                results: dict = actor.extra.setdefault("check_results", {})
                results[str(target.user_id)] = {
                    "name": target.first_name,
                    "role": revealed,
                }

        # 11. Journalist check
        from app.core.roles.journalist import JournalistRole

        for a in active_actions:
            if a.action_type == "check" and a.role == "journalist" and a.target_id is not None:
                target = state.get_player(a.target_id)
                actor = state.get_player(a.actor_id)
                if target is None or actor is None:
                    continue
                if target.role in ("detective", "sergeant"):
                    revealed = "citizen"
                elif target.role in JournalistRole.DETECTABLE_ROLES:
                    revealed = target.role
                else:
                    revealed = "citizen"
                outcome.journalist_results.append(
                    CheckResult(
                        actor_id=actor.user_id,
                        target_id=target.user_id,
                        target_name=target.first_name,
                        revealed_role=revealed,
                        revealed_team=Team.CITIZENS if revealed == "citizen" else target.team,
                        by="journalist",
                    )
                )

        # 12a. Crook (Aferist) — record proxy_target for next day's voting
        for a in active_actions:
            if a.role == "crook" and a.action_type == "visit" and a.target_id is not None:
                actor = state.get_player(a.actor_id)
                if actor is not None:
                    actor.extra["proxy_target"] = a.target_id

        # 12. Snitch reveal
        for a in active_actions:
            if a.role != "snitch" or a.target_id is None:
                continue
            target = state.get_player(a.target_id)
            if target is None:
                continue
            if "mask" in target.items_active:
                continue
            for det_act in active_actions:
                if (
                    det_act.role == "detective"
                    and det_act.action_type == "check"
                    and det_act.target_id == a.target_id
                ):
                    snitch = state.get_player(a.actor_id)
                    if snitch is None:
                        break
                    revealed = self._reveal_role_for_detective(target, lawyer_protected)
                    outcome.snitch_reveals.append(
                        SnitchReveal(
                            snitch_id=a.actor_id,
                            target_id=target.user_id,
                            target_name=target.first_name,
                            revealed_role=revealed,
                        )
                    )
                    snitch.extra["snitch_revealed_count"] = (
                        snitch.extra.get("snitch_revealed_count", 0) + 1
                    )
                    break

        # 13. Hobo witness
        for hobo_id, target_id in hobo_visits.items():
            target = state.get_player(target_id)
            if target is None:
                continue
            if target_id in outcome.deaths:
                killer_role = self._find_killer_role(active_actions, target_id)
                blocked = (killer_role is not None) and self._killer_has_mask(
                    state, active_actions, target_id
                )
                outcome.hobo_results.append(
                    HoboResult(
                        actor_id=hobo_id,
                        target_id=target_id,
                        target_name=target.first_name,
                        target_died=True,
                        killer_role=None if blocked else killer_role,
                        blocked_by_mask=blocked,
                    )
                )
            else:
                outcome.hobo_results.append(
                    HoboResult(
                        actor_id=hobo_id,
                        target_id=target_id,
                        target_name=target.first_name,
                        target_died=False,
                        killer_role=None,
                        blocked_by_mask=False,
                    )
                )

        # 14. Sergeant promotion
        self._promote_sergeant_if_needed(state, outcome)

        # 15. Persist round log
        round_log = state.current_round()
        round_log.night_actions = list(state.current_actions.values())
        round_log.night_deaths = outcome.deaths
        state.current_actions = {}
        return outcome

    # === Helpers ===

    def _priority(self, a: NightAction) -> int:
        order = {
            "sleep": 10,
            "visit": 20,
            "queue": 25,
            "final_night": 25,
            "kill": 30,
            "protect": 35,
            "heal": 40,
            "check": 50,
        }
        return order.get(a.action_type, 100)

    def _death_reason_for_role(self, role: str) -> DeathReason:
        return {
            "don": DeathReason.KILLED_MAFIA,
            "mafia": DeathReason.KILLED_MAFIA,
            "killer": DeathReason.KILLED_KILLER,
            "detective": DeathReason.KILLED_DETECTIVE,
            "maniac": DeathReason.KILLED_MANIAC,
        }.get(role, DeathReason.KILLED_MAFIA)

    def _hooker_blocked_by_don(self, state: GameState, hooker_action: NightAction) -> bool:
        if hooker_action.target_id is None:
            return True
        target = state.get_player(hooker_action.target_id)
        if target is None or target.role != "don":
            return False
        don_action = state.current_actions.get(hooker_action.target_id)
        if don_action is None:
            return False
        return don_action.target_id == hooker_action.actor_id

    def _role_pierces_shields(self, role_code: str) -> bool:
        from app.core.roles import get_role

        role = get_role(role_code)
        return getattr(role, "pierces_shields", False)

    def _reveal_role_for_detective(self, target: PlayerState, lawyer_protected: set[int]) -> str:
        if "fake_document" in target.items_active:
            return "citizen"
        if target.user_id in lawyer_protected and target.team == Team.MAFIA:
            return "citizen"
        if target.role == "kamikaze":
            return "citizen"
        return target.role

    def _find_killer_role(self, actions: list[NightAction], target_id: int) -> str | None:
        for a in actions:
            if a.action_type == "kill" and a.target_id == target_id:
                return a.role
        return None

    def _killer_has_mask(
        self, state: GameState, actions: list[NightAction], target_id: int
    ) -> bool:
        for a in actions:
            if a.action_type == "kill" and a.target_id == target_id:
                killer = state.get_player(a.actor_id)
                if killer and "mask" in killer.items_active:
                    return True
        return False

    def _handle_werewolf_attack(
        self,
        state: GameState,
        target: PlayerState,
        attackers: list[tuple[str, int, NightAction]],
        outcome: NightOutcome,
    ) -> None:
        attacker_roles = {role for role, _, _ in attackers}

        if "killer" in attacker_roles or "maniac" in attacker_roles:
            target.alive = False
            target.died_at_round = state.round_num
            target.died_at_phase = Phase.NIGHT
            target.died_reason = DeathReason.KILLED_BORI
            outcome.deaths.append(target.user_id)
            outcome.death_reasons[target.user_id] = DeathReason.KILLED_BORI
            return

        if "don" in attacker_roles and "detective" in attacker_roles:
            target.alive = False
            target.died_at_round = state.round_num
            target.died_at_phase = Phase.NIGHT
            target.died_reason = DeathReason.KILLED_BORI
            outcome.deaths.append(target.user_id)
            outcome.death_reasons[target.user_id] = DeathReason.KILLED_BORI
            return

        if "don" in attacker_roles:
            target.role = "mafia"
            target.team = Team.MAFIA
            outcome.transformations.append(
                TransformResult(
                    user_id=target.user_id,
                    new_role="mafia",
                    new_team=Team.MAFIA,
                    by_role="don",
                )
            )
            return
        if "detective" in attacker_roles:
            target.role = "sergeant"
            target.team = Team.CITIZENS
            outcome.transformations.append(
                TransformResult(
                    user_id=target.user_id,
                    new_role="sergeant",
                    new_team=Team.CITIZENS,
                    by_role="detective",
                )
            )
            return

    def _promote_sergeant_if_needed(self, state: GameState, outcome: NightOutcome) -> None:
        detectives_alive = [p for p in state.alive_players() if p.role == "detective"]
        if detectives_alive:
            return
        sergeants = [p for p in state.alive_players() if p.role == "sergeant"]
        if not sergeants:
            return
        sergeant = sergeants[0]
        sergeant.role = "detective"
        outcome.transformations.append(
            TransformResult(
                user_id=sergeant.user_id,
                new_role="detective",
                new_team=Team.CITIZENS,
                by_role="auto-promotion",
            )
        )
        logger.info(f"Sergeant {sergeant.user_id} promoted to Detective")


# === Public helpers ===


def collect_night_actor_ids(state: GameState) -> list[int]:
    from app.core.roles import get_role

    return [p.user_id for p in state.alive_players() if get_role(p.role).has_night_action]


def _is_protected_by_lawyer(state: GameState, target_id: int) -> bool:
    for action in state.current_actions.values():
        if action.role == "lawyer" and action.target_id == target_id:
            return True
    return False
