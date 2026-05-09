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
from app.core.state import GameState
from app.services.i18n_service import get_translator
from app.services.messaging import role_emoji_name


async def send_role_feedback(bot: Bot, state: GameState, outcome: NightOutcome) -> None:
    """Send all role-specific DMs after night resolution."""
    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    coros = []

    # Detective results
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

    # Doctor results
    for h in outcome.doctor_results:
        if h.visited_by_killers:
            visitor_roles = ", ".join(role_emoji_name(r, locale) for r in h.visited_by_killers)
            text = _("feedback-doctor-saved", target=h.target_name, visitors=visitor_roles)
        else:
            text = _("feedback-doctor-no-visitors", target=h.target_name)
        coros.append(_safe_dm(bot, h.actor_id, text))

    # Hooker results — confirm to actor + DM target
    for hr in outcome.hooker_results:
        coros.append(
            _safe_dm(
                bot,
                hr.actor_id,
                _("feedback-hooker-confirm", target=hr.target_name),
            )
        )
        coros.append(_safe_dm(bot, hr.target_id, _("feedback-hooker-target")))

    if coros:
        await asyncio.gather(*coros, return_exceptions=True)


async def _safe_dm(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(user_id, text)
    except TelegramForbiddenError:
        logger.debug(f"Cannot DM user {user_id} (blocked)")
    except Exception as e:
        logger.warning(f"DM error for {user_id}: {e}")
