"""🤦🏼 Suicide (Suidsid) — singleton.

Win condition: voted out at the day phase wins solo. Killed at night —
or surviving the whole game without being voted out — loses. Despite
appearing as "Tinch aholi" to the Komissar (handled separately in the
night-resolver), his team membership is SINGLETON: he never shares the
citizen victory.

The actual solo-win detection happens in `core/win_conditions.py` —
`winner_user_ids(SINGLETON)` includes him only when
`died_at_phase == "voting"`.
"""

from app.core.roles.base import BaseRole
from app.core.state import Team


class SuicideRole(BaseRole):
    code = "suicide"
    team = Team.SINGLETON
    has_night_action = False
    night_message_key = None

    def night_prompt_key(self) -> str | None:
        return None
