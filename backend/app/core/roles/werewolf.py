"""🐺 Werewolf (Bo'ri) — transformatsiya rolini.

- Don otsa → keyingi tundan Mafiyaga aylanadi
- Komissar otsa → keyingi tundan Serjantga aylanadi
- Qotil/Ninza o'ldirsa → o'ladi
- Don+Komissar baravar → o'ladi
- Osilsa → mag'lub
"""

from app.core.roles.base import BaseRole
from app.core.state import Team


class WerewolfRole(BaseRole):
    code = "werewolf"
    team = Team.SINGLETON
    has_night_action = False  # passive — reaction-only
    night_message_key = "night-action-msg-werewolf"

    def night_prompt_key(self) -> str | None:
        return None
