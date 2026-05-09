"""👩🏼‍💻 Journalist — mafia spy, har tun 1 odamni tekshiradi.

- Doktor, Daydi, Kezuvchi, Advokat, Maniak, G'azabkorni topa oladi
- Komissar va uning mehmonlarini ko'rmaydi (Komissarni topib bera olmaydi)
"""

from typing import ClassVar

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class JournalistRole(BaseRole):
    code = "journalist"
    team = Team.MAFIA
    has_night_action = True
    night_action_priority = 50  # check (parallel to detective)
    night_message_key = "night-action-msg-journalist"

    # Roles journalist CAN reveal
    DETECTABLE_ROLES: ClassVar[set[str]] = {
        "doctor",
        "hobo",
        "hooker",
        "lawyer",
        "maniac",
        "arsonist",
        "killer",
        "werewolf",
        "mage",
        "kamikaze",
    }

    def night_prompt_key(self) -> str | None:
        return "night-prompt-journalist"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        return target.alive and target.user_id != actor.user_id
