"""🥷 Killer (Ninza) — mafia tomonida, doktor davolashini teshib o'tadi.

- Doktor davolaganini teshib o'tadi (shifokor saqlay olmaydi).
- Shield va Killer Shield Ninza hujumini ushlab qoladi
  (faqat 🔫 Miltiq bu himoyalarni ham teshib o'tadi).
- Kezuvchi (Hooker) Ninzani uxlata olmaydi.
"""

from app.core.roles.base import BaseRole
from app.core.state import GameState, PlayerState, Team


class KillerRole(BaseRole):
    code = "killer"
    team = Team.MAFIA
    has_night_action = True
    night_action_priority = 25  # before doctor heal (40), kills first
    night_message_key = "night-action-msg-killer"
    # Killer no longer auto-pierces shields. Only the 🔫 Miltiq item does
    # (and only when the player confirms via the Ha/Yo'q gate). What's
    # intrinsic to Killer is anti-doctor: a Doctor heal cannot save
    # Killer's victim. Shield / killer_shield still trigger normally.
    pierces_shields = False
    pierces_doctor_heal = True

    def night_prompt_key(self) -> str | None:
        return "night-prompt-killer"

    def can_target(self, state: GameState, actor: PlayerState, target: PlayerState) -> bool:
        return target.alive and target.user_id != actor.user_id and target.team != Team.MAFIA
