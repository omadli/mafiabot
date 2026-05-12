"""AFK tracker — kick players who skip 2 consecutive phases without action."""

from __future__ import annotations

from aiogram import Bot
from loguru import logger

from app.core.state import DeathReason, GameState, Phase
from app.db.models import User
from app.services import game_service
from app.services.i18n_service import get_translator
from app.services.messaging import _safe_send, player_mention, role_emoji_name


async def track_phase_inactivity(bot: Bot, state: GameState, ended_phase: Phase) -> None:
    """Called after each phase ends. Increments skipped_phases for inactive players.

    Called from PhaseManager hook after night/voting phases.
    """
    afk_settings = state.settings.get("afk", {})
    threshold = afk_settings.get("skip_phases_before_kick", 2)
    xp_penalty = afk_settings.get("xp_penalty_on_kick", 50)

    locale = state.settings.get("language", "uz")
    _ = get_translator(locale)

    to_kick: list[int] = []

    # Whom did Kezuvchi (Hooker) put to sleep this night? Sleeping players
    # are physically unable to act and must NOT count toward AFK strikes.
    slept_user_ids: set[int] = set()
    if ended_phase == Phase.NIGHT:
        for action in state.current_actions.values():
            if action.role == "hooker" and action.action_type == "sleep" and action.target_id:
                slept_user_ids.add(action.target_id)

    for player in state.alive_players():
        # Did player act this phase?
        acted = False
        if ended_phase == Phase.NIGHT:
            acted = player.user_id in state.current_actions
        elif ended_phase == Phase.VOTING:
            acted = player.user_id in state.current_votes

        if acted:
            player.skipped_phases = 0
        else:
            # Citizens at night don't have action — skip them
            from app.core.roles import get_role

            role = get_role(player.role)
            if ended_phase == Phase.NIGHT and not role.has_night_action:
                continue

            # Hooker-slept players couldn't act — don't penalise them
            if ended_phase == Phase.NIGHT and player.user_id in slept_user_ids:
                continue

            player.skipped_phases += 1
            logger.debug(
                f"Player {player.user_id} skipped phase ({player.skipped_phases}/{threshold})"
            )
            if player.skipped_phases >= threshold:
                to_kick.append(player.user_id)

    # Kick AFK players
    for user_id in to_kick:
        await _kick_afk_player(bot, state, user_id, xp_penalty, _, locale)


async def _kick_afk_player(
    bot: Bot, state: GameState, user_id: int, xp_penalty: int, _, locale: str = "uz"
) -> None:
    player = state.get_player(user_id)
    if player is None or not player.alive:
        return

    player.alive = False
    player.died_at_round = state.round_num
    player.died_at_phase = state.phase
    player.died_reason = DeathReason.AFK_KICKED

    # Penalty
    user = await User.get_or_none(id=user_id)
    if user is not None:
        user.xp = max(0, user.xp - xp_penalty)
        user.afk_warnings += 1
        await user.save(update_fields=["xp", "afk_warnings"])

    await game_service.set_user_active_game(user_id, None)

    # Comedic last-words broadcast (rumor style — @MafiaAzBot parity):
    #   "Aholidan kimdir 🤵🏻 Don <mention> o'limidan oldin:
    #    Men o'yin paytida boshqa uxlamayma-a-a-a-a-a-an! deb qichqirganini eshitgan."
    mention = player_mention(user_id, player.first_name)
    show_role_on_death = state.settings.get("display", {}).get("show_role_on_death", True)
    role_label = (
        role_emoji_name(player.role, locale) if (show_role_on_death and player.role) else ""
    )
    text = _("afk-last-words", role=role_label, mention=mention)
    await _safe_send(bot, state.chat_id, text)
    logger.info(f"AFK kicked user {user_id} from game {state.id}")
