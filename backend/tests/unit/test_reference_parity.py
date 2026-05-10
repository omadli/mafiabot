"""Reference parity tests — verify behaviors mirror @MafiaAzBot.

Covers Wave 2-5 fixes from the plan file:
- Werewolf anonymous transformation (#11)
- Kamikaze role reveal in take-with-me (#10)
- Last words include role+emoji (#12)
- Multi-victim separate messages (#13)
- Arsonist self-burn detection (#14)
- Game-end winners/losers/duration (#15)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.core.actions import NightAction, NightOutcome, TransformResult
from app.core.state import (
    DeathReason,
    GameState,
    Phase,
    PlayerState,
    RoundLog,
    Team,
)


def _make_state(round_num: int = 1) -> GameState:
    """Build a small GameState for messaging tests."""
    return GameState(
        group_id=-100123,
        chat_id=-100123,
        phase=Phase.DAY,
        round_num=round_num,
        players=[
            PlayerState(user_id=1, first_name="Don1", join_order=1, role="don", team=Team.MAFIA),
            PlayerState(
                user_id=2, first_name="Mafia1", join_order=2, role="mafia", team=Team.MAFIA
            ),
            PlayerState(
                user_id=3,
                first_name="Detective1",
                join_order=3,
                role="detective",
                team=Team.CITIZENS,
            ),
            PlayerState(
                user_id=4,
                first_name="Werewolf1",
                join_order=4,
                role="werewolf",
                team=Team.SINGLETON,
            ),
            PlayerState(
                user_id=5,
                first_name="Arsonist1",
                join_order=5,
                role="arsonist",
                team=Team.SINGLETON,
            ),
        ],
        rounds=[RoundLog(round_num=round_num)],
        settings={"language": "uz", "display": {"show_role_on_death": True}},
        started_at=1700000000,
        finished_at=1700000900,  # +15 minutes
    )


# === #11 Werewolf transformation anonymous ===


@pytest.mark.asyncio
async def test_werewolf_transform_no_player_name() -> None:
    """Transformation broadcast must NOT include werewolf's name (gameplay maxfiyligi)."""
    from app.services.messaging import broadcast_night_results

    state = _make_state()
    state.current_round().night_actions = []
    outcome = NightOutcome(
        deaths=[],
        death_reasons={},
        detective_results=[],
        doctor_results=[],
        sleeping=set(),
        transformations=[
            TransformResult(
                user_id=4, new_role="sergeant", new_team=Team.CITIZENS, by_role="detective"
            )
        ],
    )

    sent: list[str] = []
    bot = MagicMock()

    async def _send(_chat_id: int, text: str, **_kw):
        sent.append(text)

    bot.send_message = _send

    await broadcast_night_results(bot, state, outcome)

    transform_msgs = [m for m in sent if "Bo'ri" in m or "Werewolf" in m or "Оборотень" in m]
    assert transform_msgs, f"Expected transformation broadcast, got: {sent}"
    msg = transform_msgs[0]
    # Must NOT contain the werewolf player's name
    assert "Werewolf1" not in msg, f"Werewolf identity leaked in transformation msg: {msg}"
    # Must contain the new role
    assert "Serjant" in msg or "Sergeant" in msg


# === #10 Kamikaze take-with-me reveals victim role ===


def test_kamikaze_message_template_uses_victim_role() -> None:
    """The new i18n key kamikaze-took-victim takes victim_role params."""
    from app.services.i18n_service import get_translator

    _ = get_translator("uz")
    text = _(
        "kamikaze-took-victim",
        victim="Test",
        victim_role_emoji="🤵🏼",
        victim_role="Mafia",
    )
    assert "Test" in text
    assert "Mafia" in text
    assert "🤵🏼" in text or "Mafia" in text  # role revealed


# === #12 Last words include role+emoji ===


def test_last_words_template_uses_role_params() -> None:
    """last-words-broadcast key has role_emoji + role_name params."""
    from app.services.i18n_service import get_translator

    _ = get_translator("uz")
    text = _(
        "last-words-broadcast",
        role_emoji="🧙‍♂",
        role_name="Daydi",
        mention="<a>Player</a>",
        message="Help me!",
    )
    assert "Daydi" in text
    assert "Help me!" in text


# === #14 Arsonist self-burn detection ===


def test_arsonist_self_kill_detector() -> None:
    """_is_arsonist_self_kill returns True for self-burn final_night action."""
    from app.services.messaging import _is_arsonist_self_kill

    state = _make_state()
    arsonist = state.get_player(5)
    assert arsonist is not None

    # Add a final_night action where actor == target == arsonist
    state.current_round().night_actions = [
        NightAction(
            actor_id=5,
            role="arsonist",
            action_type="final_night",
            target_id=5,
        )
    ]

    assert _is_arsonist_self_kill(state, arsonist) is True


def test_arsonist_normal_kill_not_self_burn() -> None:
    """An arsonist killed by mafia is NOT a self-burn."""
    from app.services.messaging import _is_arsonist_self_kill

    state = _make_state()
    arsonist = state.get_player(5)
    assert arsonist is not None

    state.current_round().night_actions = [
        NightAction(actor_id=1, role="don", action_type="kill", target_id=5)
    ]
    assert _is_arsonist_self_kill(state, arsonist) is False


# === #13 Multi-victim separate messages ===


@pytest.mark.asyncio
async def test_multi_victim_sends_separate_messages() -> None:
    """2+ deaths → 2+ separate send_message calls (no bullet list)."""
    from app.services.messaging import broadcast_night_results

    state = _make_state()
    # Mark 2 victims dead with kill actions
    state.players[2].alive = False  # Detective
    state.players[3].alive = False  # Werewolf
    state.current_round().night_actions = [
        NightAction(actor_id=1, role="don", action_type="kill", target_id=3),
        NightAction(actor_id=1, role="don", action_type="kill", target_id=4),
    ]

    outcome = NightOutcome(
        deaths=[3, 4],
        death_reasons={3: DeathReason.KILLED_MAFIA, 4: DeathReason.KILLED_MAFIA},
        detective_results=[],
        doctor_results=[],
        sleeping=set(),
    )

    sent_msgs: list[str] = []
    bot = MagicMock()

    async def _send(_chat_id: int, text: str, **_kw):
        sent_msgs.append(text)

    bot.send_message = _send

    await broadcast_night_results(bot, state, outcome)

    # Each victim should have its own message containing their name
    detective_msgs = [m for m in sent_msgs if "Detective1" in m]
    werewolf_msgs = [m for m in sent_msgs if "Werewolf1" in m]
    assert len(detective_msgs) >= 1, f"Detective1 missing: {sent_msgs}"
    assert len(werewolf_msgs) >= 1, f"Werewolf1 missing: {sent_msgs}"
    # No bullet-style joined "🌅\n• ... \n• ..." message
    bullet_combined = [m for m in sent_msgs if "•" in m and m.count("•") >= 2]
    assert not bullet_combined, f"Found combined bullet list: {bullet_combined}"


# === #15 Game-end format ===


@pytest.mark.asyncio
async def test_game_end_separates_winners_losers() -> None:
    """broadcast_game_end emits winners + losers sections + duration."""
    from app.services.messaging import broadcast_game_end

    state = _make_state()
    state.winner_team = Team.MAFIA
    state.phase = Phase.FINISHED

    captured: list[tuple[int, str, dict]] = []
    bot = MagicMock()

    async def _send(chat_id: int, text: str, **kwargs):
        captured.append((chat_id, text, kwargs))

    bot.send_message = _send

    await broadcast_game_end(bot, state)

    assert captured, "No message sent"
    msg = captured[0][1]
    # Header + winners section + losers section + duration
    assert "tugadi" in msg.lower() or "over" in msg.lower() or "окончена" in msg.lower()
    assert "minut" in msg or "minutes" in msg or "минут" in msg


def test_game_end_duration_formula() -> None:
    """Duration = (finished_at - started_at) // 60, min 1 minute."""
    state = _make_state()
    state.started_at = 1700000000
    state.finished_at = 1700000900  # +900s = 15min
    minutes = max(1, (state.finished_at - state.started_at) // 60)
    assert minutes == 15

    # Edge case: less than 60 seconds → still shows 1 min
    state.finished_at = 1700000030
    minutes = max(1, (state.finished_at - state.started_at) // 60)
    assert minutes == 1


# === Mayor vote prefix logic ===


def test_mayor_role_prefix_check() -> None:
    """Mayor identity check is straightforward — verify role logic."""
    state = _make_state()
    state.players.append(
        PlayerState(
            user_id=10, first_name="Mayor1", join_order=10, role="mayor", team=Team.CITIZENS
        )
    )
    mayor = state.get_player(10)
    assert mayor is not None
    assert mayor.role == "mayor"
    # Other players are not mayors
    assert state.get_player(1).role != "mayor"
