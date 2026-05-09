"""👮🏻‍♂ Sergeant — komissar yordamchisi, komissar o'lsa o'rnini egallaydi."""

from app.core.roles.base import BaseRole
from app.core.state import Team


class SergeantRole(BaseRole):
    code = "sergeant"
    team = Team.CITIZENS
    has_night_action = False  # passive until Detective dies
    night_message_key = None

    def night_prompt_key(self) -> str | None:
        return None
