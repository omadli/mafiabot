"""🤓 Snitch (Sotqin) — komissar bilan bir target tekshirsa rolni guruhga oshkor qiladi.

- Har tun 1 odamni tanlaydi
- Agar Komissar ham aynan shu odamni tekshirsa → guruhga rolni e'lon qiladi
- Maska himoyasi bo'lsa Sotqin ham ko'rmaydi
- Kamida 1 marta oshkor qilsa g'olib
"""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class SnitchRole(BaseRole):
    code = "snitch"
    team = Team.SINGLETON
    has_night_action = True
    night_action_priority = 55  # after detective check (50)
    night_message_key = "night-action-msg-snitch"

    def night_prompt_key(self) -> str | None:
        return "night-prompt-snitch"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        return target.alive and target.user_id != actor.user_id
