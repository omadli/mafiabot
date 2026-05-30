"""Send private DM feedback to players after each night resolution.

- Detective: result of check (target's revealed role)
- Doctor: who they healed and visitors (killers attempted)
- Hooker: confirms target slept
- Hooker target: receives "ana 💊 dori..." message
"""

from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger

from app.core.actions import NightOutcome
from app.core.state import DeathReason, GameState, Team
from app.services.i18n_service import get_translator
from app.services.messaging import player_mention, role_emoji_name


async def send_role_feedback(bot: Bot, state: GameState, outcome: NightOutcome) -> None:
    """Send all role-specific DMs after night resolution."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    coros = []

    # Detective results — DM the Detective with their finding, and a
    # blind heads-up to the target ("someone got curious about your role").
    # Multiple Detectives (e.g. Sergeant promoted) all check independently;
    # if multiple checked the same target, the target receives one DM per
    # check, which intentionally signals heavier attention.
    for r in outcome.detective_results:
        coros.append(
            _safe_dm(
                bot,
                r.actor_id,
                _(
                    "feedback-detective-result",
                    target=r.target_name,
                    role=role_emoji_name(r.revealed_role, locale),
                ),
            )
        )
        coros.append(_safe_dm(bot, r.target_id, _("feedback-detective-target-notice")))

    # Doctor results
    #   saved=True  → DM doctor "you healed {target}, visitor was {killer}"
    #                 AND DM target "Doctor healed you" (target was attacked).
    #   saved=False → DM doctor "no visitors today". Then the target DM
    #                 splits on whether they were a kill/sleep target this
    #                 night despite the doctor's heal:
    #                   - hooker tried to sleep them → "Doctor healed you"
    #                   - nobody touched them → "Doctor came to visit you"
    for h in outcome.doctor_results:
        if h.saved:
            visitor_roles = ", ".join(role_emoji_name(r, locale) for r in h.visited_by_killers)
            text = _("feedback-doctor-saved", target=h.target_name, visitors=visitor_roles)
            target_text = _("feedback-doctor-target-saved")
        else:
            text = _("feedback-doctor-no-visitors")
            # Was the target also hit by a hooker (or any non-doctor action)?
            target_threatened = any(
                a.target_id == h.target_id
                and a.action_type in ("kill", "sleep")
                and a.actor_id != h.actor_id
                for a in state.current_actions.values()
            )
            target_text = _(
                "feedback-doctor-target-saved"
                if target_threatened
                else "feedback-doctor-target-visit"
            )
        coros.append(_safe_dm(bot, h.actor_id, text, parse_mode="HTML"))
        # Don't tell the doctor about themselves: skip the target DM when
        # the doctor self-healed.
        if h.target_id != h.actor_id:
            coros.append(_safe_dm(bot, h.target_id, target_text))

    # Hooker results — confirm to actor + DM target.
    # The Hooker always gets confirmation (so they don't get info on
    # which targets are premium); the target is only DMed when they
    # actually went to sleep — premium players who shrugged off the
    # visit silently act normally.
    for hr in outcome.hooker_results:
        coros.append(
            _safe_dm(
                bot,
                hr.actor_id,
                _("feedback-hooker-confirm", target=hr.target_name),
            )
        )
        if not hr.blocked:
            coros.append(_safe_dm(bot, hr.target_id, _("feedback-hooker-target")))

    # Shield saves — DM the target. The narrative line depends on which
    # shield triggered (and which attacker role it absorbed). The group
    # message is anonymous ("Kimdir himoyasini ishlatdi!") — broadcasted
    # separately by messaging.broadcast_night_results.
    for s in outcome.shield_saves:
        if s.item == "fake_document":
            text = _("feedback-fake-document-used")
        elif s.item == "killer_shield":
            text = _("feedback-killer-shield-used")
        else:  # 'shield'
            text = _("feedback-shield-used")
        coros.append(_safe_dm(bot, s.target_id, text))

    if coros:
        await asyncio.gather(*coros, return_exceptions=True)

    # Mafia-team kill announcement (DM to every alive mafia member):
    # if mafia successfully killed someone this night, all surviving mafia
    # members get a DM celebrating it — keeps the team in sync.
    await _broadcast_mafia_kill(bot, state, outcome, locale)

    # Mafia team picked targets but couldn't reach consensus — DM every
    # alive mafia member so they understand why nobody died by their hands.
    if outcome.mafia_no_consensus:
        await _broadcast_mafia_no_consensus(bot, state, locale)


async def _broadcast_mafia_no_consensus(bot: Bot, state: GameState, locale: str) -> None:
    t = get_translator(locale)
    alive_mafia_ids = [p.user_id for p in state.alive_players() if p.team == Team.MAFIA]
    if not alive_mafia_ids:
        return
    text = t("mafia-no-consensus-dm")

    async def _dm(uid: int) -> None:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
        except TelegramForbiddenError:
            pass
        except Exception as e:
            logger.debug(f"Mafia no-consensus DM to {uid} failed: {e}")

    await asyncio.gather(*(_dm(uid) for uid in alive_mafia_ids), return_exceptions=True)


async def _broadcast_mafia_kill(
    bot: Bot, state: GameState, outcome: NightOutcome, locale: str
) -> None:
    """DM living mafia about any victim that died by mafia hands tonight."""
    mafia_victims: list[int] = [
        vid for vid in outcome.deaths if outcome.death_reasons.get(vid) == DeathReason.KILLED_MAFIA
    ]
    if not mafia_victims:
        return

    t = get_translator(locale)
    alive_mafia_ids = [p.user_id for p in state.alive_players() if p.team == Team.MAFIA]
    if not alive_mafia_ids:
        return

    lines: list[str] = []
    for vid in mafia_victims:
        victim = state.get_player(vid)
        if victim is None:
            continue
        lines.append(t("mafia-kill-broadcast", mention=player_mention(vid, victim.first_name)))
    if not lines:
        return
    text = "\n".join(lines)

    async def _dm(uid: int) -> None:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
        except TelegramForbiddenError:
            pass
        except Exception as e:
            logger.debug(f"Mafia kill DM to {uid} failed: {e}")

    await asyncio.gather(*(_dm(uid) for uid in alive_mafia_ids), return_exceptions=True)


async def _safe_dm(bot: Bot, user_id: int, text: str, parse_mode: str | None = None) -> None:
    try:
        await bot.send_message(user_id, text, parse_mode=parse_mode)
    except TelegramForbiddenError:
        logger.debug(f"Cannot DM user {user_id} (blocked)")
    except Exception as e:
        logger.warning(f"DM error for {user_id}: {e}")
