"""🧟 Arsonist (G'azabkor) — har tun 1 odamni tanlaydi.

- target_queue ga qo'shadi
- "Oxirgi tun" tugmasini bossa — barcha tanlaganlarni o'ldiradi
- 3+ odam o'ldirolsa g'olib
"""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class ArsonistRole(BaseRole):
    code = "arsonist"
    team = Team.SINGLETON
    has_night_action = True
    night_action_priority = 25  # queue before main kills
    night_message_key = "night-action-msg-arsonist"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-arsonist"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        if not target.alive:
            return False
        # Cannot target self (only via "Oxirgi tun" button)
        if target.user_id == actor.user_id:
            return False
        # Cannot target same player twice
        queue = actor.extra.get("target_queue", [])
        return target.user_id not in queue
