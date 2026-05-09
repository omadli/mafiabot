"""🥷 Killer (Ninza) — mafia tomonida, himoyalarni teshib o'tadi.

- Doktor davolaganini ham, Shield ham, Killer Shield ham — hammasini teshib o'tadi.
- Faqat osish yoki Komissar bilan o'zaro hujum o'ldira oladi.
"""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class KillerRole(BaseRole):
    code = "killer"
    team = Team.MAFIA
    has_night_action = True
    night_action_priority = 25  # before doctor heal (40), kills first
    night_message_key = "night-action-msg-killer"
    pierces_shields = True  # himoyalarni teshib o'tadi

    def night_prompt_key(self) -> str | None:
        return "night-prompt-killer"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        return target.alive and target.user_id != actor.user_id and target.team != Team.MAFIA
