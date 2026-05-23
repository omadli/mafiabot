"""Regression tests for the bug fixes shipped in commit 532ad74.

Covers:
  * Bug 3 — shield/killer_shield/fake_document saves are recorded in
    NightOutcome.shield_saves with the correct attacker_role.
  * Bug 5 — premium players: shield/killer_shield save TWICE before the
    item is consumed; Hooker visit is recorded with `blocked=True` and
    does NOT mark the target as sleeping.
"""

from __future__ import annotations

from app.core.actions import ActionResolver, ShieldSave
from app.core.state import (
    GameState,
    NightAction,
    Phase,
    PlayerState,
    Team,
)


def _state_with(players: list[PlayerState], actions: list[NightAction]) -> GameState:
    state = GameState(
        group_id=-1,
        chat_id=-1,
        phase=Phase.NIGHT,
        round_num=1,
        players=players,
        current_actions={a.actor_id: a for a in actions},
    )
    # Force round-1 log to exist so resolver can write into current_round().
    state.current_round()
    return state


# === Bug 3: shield saves recorded ===


def test_shield_save_recorded_when_don_attacks_shielded_citizen():
    target = PlayerState(
        user_id=10,
        first_name="Civ",
        join_order=1,
        role="citizen",
        team=Team.CITIZENS,
        items_active=["shield"],
    )
    attacker = PlayerState(user_id=20, first_name="Don", join_order=2, role="don", team=Team.MAFIA)
    actions = [NightAction(actor_id=20, role="don", action_type="kill", target_id=10)]
    state = _state_with([target, attacker], actions)

    outcome = ActionResolver().resolve(state)

    assert outcome.deaths == []
    assert len(outcome.shield_saves) == 1
    save = outcome.shield_saves[0]
    assert save.target_id == 10
    assert save.item == "shield"
    assert save.attacker_role == "don"
    # Item consumed for non-premium target.
    assert "shield" not in state.get_player(10).items_active


def test_killer_shield_blocks_killer_only():
    target = PlayerState(
        user_id=10,
        first_name="Civ",
        join_order=1,
        role="citizen",
        team=Team.CITIZENS,
        items_active=["killer_shield"],
    )
    killer = PlayerState(
        user_id=20, first_name="Ninza", join_order=2, role="killer", team=Team.MAFIA
    )
    actions = [NightAction(actor_id=20, role="killer", action_type="kill", target_id=10)]
    state = _state_with([target, killer], actions)

    outcome = ActionResolver().resolve(state)

    assert outcome.deaths == []
    assert len(outcome.shield_saves) == 1
    assert outcome.shield_saves[0].item == "killer_shield"


def test_fake_document_records_save_when_role_concealed():
    # Detective checks a Don who has a fake_document — revealed role is
    # "citizen" so the Don should get a save event for the DM heads-up.
    don = PlayerState(
        user_id=10,
        first_name="Don",
        join_order=1,
        role="don",
        team=Team.MAFIA,
        items_active=["fake_document"],
    )
    det = PlayerState(
        user_id=20,
        first_name="Kom",
        join_order=2,
        role="detective",
        team=Team.CITIZENS,
    )
    actions = [NightAction(actor_id=20, role="detective", action_type="check", target_id=10)]
    state = _state_with([don, det], actions)

    outcome = ActionResolver().resolve(state)

    assert len(outcome.detective_results) == 1
    assert outcome.detective_results[0].revealed_role == "citizen"
    fake_saves = [s for s in outcome.shield_saves if s.item == "fake_document"]
    assert len(fake_saves) == 1
    assert fake_saves[0].target_id == 10


def test_fake_document_no_save_for_actual_citizen():
    # A real citizen with fake_document → no concealment happened, so no
    # save event is recorded (would be a misleading DM).
    civ = PlayerState(
        user_id=10,
        first_name="Civ",
        join_order=1,
        role="citizen",
        team=Team.CITIZENS,
        items_active=["fake_document"],
    )
    det = PlayerState(
        user_id=20,
        first_name="Kom",
        join_order=2,
        role="detective",
        team=Team.CITIZENS,
    )
    actions = [NightAction(actor_id=20, role="detective", action_type="check", target_id=10)]
    state = _state_with([civ, det], actions)

    outcome = ActionResolver().resolve(state)
    assert all(s.item != "fake_document" for s in outcome.shield_saves)


def test_rifle_pierces_shield_no_save_recorded():
    # Rifle bypasses every defence — the kill lands and no shield_save
    # event is recorded (the item is NOT consumed by piercing attacks).
    target = PlayerState(
        user_id=10,
        first_name="Civ",
        join_order=1,
        role="citizen",
        team=Team.CITIZENS,
        items_active=["shield"],
    )
    don = PlayerState(user_id=20, first_name="Don", join_order=2, role="don", team=Team.MAFIA)
    actions = [
        NightAction(actor_id=20, role="don", action_type="kill", target_id=10, used_item="rifle")
    ]
    state = _state_with([target, don], actions)

    outcome = ActionResolver().resolve(state)
    assert outcome.deaths == [10]
    assert outcome.shield_saves == []
    # Shield slot survives — it never "triggered".
    assert "shield" in state.get_player(10).items_active


# === Bug 5: premium privileges ===


def _premium_extra() -> dict:
    return {
        "is_premium": True,
        "shield_uses_left": {"shield": 1, "killer_shield": 1, "vote_shield": 1},
    }


def test_premium_shield_saves_twice_before_consumed():
    # Night 1 — Don shoots premium target with shield. Shield catches it
    # but the item slot survives thanks to the premium bonus.
    target = PlayerState(
        user_id=10,
        first_name="VIP",
        join_order=1,
        role="citizen",
        team=Team.CITIZENS,
        items_active=["shield"],
        extra=_premium_extra(),
    )
    don = PlayerState(user_id=20, first_name="Don", join_order=2, role="don", team=Team.MAFIA)
    state = _state_with(
        [target, don],
        [NightAction(actor_id=20, role="don", action_type="kill", target_id=10)],
    )

    outcome1 = ActionResolver().resolve(state)
    assert outcome1.deaths == []
    assert len(outcome1.shield_saves) == 1
    assert "shield" in state.get_player(10).items_active  # bonus left
    assert state.get_player(10).extra["shield_uses_left"]["shield"] == 0

    # Night 2 — same attacker, same shield. The bonus is spent, so the
    # second hit also catches but THIS time the slot is consumed.
    state.current_actions = {
        20: NightAction(actor_id=20, role="don", action_type="kill", target_id=10)
    }
    state.round_num = 2
    state.current_round()

    outcome2 = ActionResolver().resolve(state)
    assert outcome2.deaths == []
    assert len(outcome2.shield_saves) == 1
    assert "shield" not in state.get_player(10).items_active  # finally gone


def test_premium_target_immune_to_hooker():
    # Hooker visits a premium target — visit is logged with blocked=True
    # and the target does NOT end up in `sleeping`. The premium target
    # can still act this night.
    premium = PlayerState(
        user_id=10,
        first_name="VIP",
        join_order=1,
        role="citizen",
        team=Team.CITIZENS,
        extra={"is_premium": True},
    )
    hooker = PlayerState(
        user_id=20,
        first_name="Kez",
        join_order=2,
        role="hooker",
        team=Team.CITIZENS,
    )
    state = _state_with(
        [premium, hooker],
        [NightAction(actor_id=20, role="hooker", action_type="sleep", target_id=10)],
    )

    outcome = ActionResolver().resolve(state)
    assert outcome.sleeping == set()
    assert len(outcome.hooker_results) == 1
    assert outcome.hooker_results[0].blocked is True
    assert outcome.hooker_results[0].target_id == 10


def test_non_premium_target_normally_slept_by_hooker():
    # Regression — make sure the premium check doesn't accidentally
    # short-circuit normal Hooker behaviour for non-premium targets.
    normie = PlayerState(
        user_id=10,
        first_name="Civ",
        join_order=1,
        role="citizen",
        team=Team.CITIZENS,
    )
    hooker = PlayerState(
        user_id=20, first_name="Kez", join_order=2, role="hooker", team=Team.CITIZENS
    )
    state = _state_with(
        [normie, hooker],
        [NightAction(actor_id=20, role="hooker", action_type="sleep", target_id=10)],
    )

    outcome = ActionResolver().resolve(state)
    assert 10 in outcome.sleeping
    assert outcome.hooker_results[0].blocked is False


# === Sanity-check the ShieldSave dataclass surface ===


def test_shield_save_dataclass_fields():
    s = ShieldSave(target_id=1, item="shield", attacker_role="don")
    assert s.target_id == 1
    assert s.item == "shield"
    assert s.attacker_role == "don"
