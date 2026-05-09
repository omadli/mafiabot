"""🤵🏼 Mafia — Donga yordam, mafia chatida ovoz."""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class MafiaRole(BaseRole):
    code = "mafia"
    team = Team.MAFIA
    has_night_action = True
    night_action_priority = 30  # same as Don
    night_message_key = "night-action-msg-don"  # umumiy "Don tanladi" xabari

    def night_prompt_key(self) -> str | None:
        return "night-prompt-mafia"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        return target.alive and target.user_id != actor.user_id and target.team != Team.MAFIA
