"""🤹 Crook (Aferist) — har tun 1 odamga tashrif, kunduzi nomidan ovoz beradi.

G'olib sharti: o'yin oxirigacha tirik qolsa.
"""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class CrookRole(BaseRole):
    code = "crook"
    team = Team.SINGLETON
    has_night_action = True
    night_action_priority = 60  # informational, late
    night_message_key = "night-action-msg-crook"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-crook"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        return target.alive and target.user_id != actor.user_id
