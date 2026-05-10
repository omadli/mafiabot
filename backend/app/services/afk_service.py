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

    # Reference parity (@MafiaAzBot): leave message reveals role
    show_role_on_death = state.settings.get("display", {}).get("show_role_on_death", True)
    mention = player_mention(user_id, player.first_name)
    if show_role_on_death and player.role:
        role_label = role_emoji_name(player.role, locale)
        role_parts = role_label.split(" ", 1)
        role_emoji = role_parts[0] if role_parts else "❓"
        role_name = role_parts[1] if len(role_parts) > 1 else player.role
        text = _(
            "leave-broadcast-with-role",
            mention=mention,
            role_emoji=role_emoji,
            role_name=role_name,
        )
    else:
        text = _("afk-kicked", mention=mention)
    await _safe_send(bot, state.chat_id, text)
    logger.info(f"AFK kicked user {user_id} from game {state.id}")
