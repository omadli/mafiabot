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


def test_fake_document_does_not_conceal_citizens_team_roles():
    # Doctor/Hooker/Lucky and other CITIZENS-team roles must NOT be hidden
    # by fake_document — the item only helps Mafia and Singletons.
    for role in ("doctor", "hooker", "lucky", "mayor", "sergeant", "hobo"):
        target = PlayerState(
            user_id=10,
            first_name="Cit",
            join_order=1,
            role=role,
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
        state = _state_with([target, det], actions)

        outcome = ActionResolver().resolve(state)
        assert len(outcome.detective_results) == 1
        assert (
            outcome.detective_results[0].revealed_role == role
        ), f"{role} should not be concealed by fake_document"
        assert all(s.item != "fake_document" for s in outcome.shield_saves)


def test_fake_document_conceals_singleton_threats():
    # Anti-civilian singletons (Maniac, Arsonist, Werewolf, Snitch) and
    # passive singletons (Mage, Crook) all benefit from fake_document.
    for role, team in (
        ("maniac", Team.SINGLETON),
        ("arsonist", Team.SINGLETON),
        ("werewolf", Team.SINGLETON),
        ("snitch", Team.SINGLETON),
        ("mage", Team.SINGLETON),
        ("crook", Team.SINGLETON),
    ):
        target = PlayerState(
            user_id=10,
            first_name="Sgl",
            join_order=1,
            role=role,
            team=team,
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
        state = _state_with([target, det], actions)

        outcome = ActionResolver().resolve(state)
        assert len(outcome.detective_results) == 1
        assert (
            outcome.detective_results[0].revealed_role == "citizen"
        ), f"{role} should be concealed by fake_document"
        fake_saves = [s for s in outcome.shield_saves if s.item == "fake_document"]
        assert len(fake_saves) == 1


def test_rifle_pierces_shield_consumes_both():
    # Rifle pierces the shield AND consumes it (the shield was destroyed).
    # The rifle slot is also burned because it had to bypass a defence.
    # No shield_save event is surfaced (target died, no "Kimdir himoyasini
    # ishlatdi" group line for an unsuccessful save).
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
    # Shield was destroyed by the rifle.
    assert "shield" not in state.get_player(10).items_active
    # Rifle was needed to pierce → consumed.
    assert outcome.rifles_consumed == [20]


def test_rifle_not_consumed_against_undefended_target():
    # No shield, no doctor → rifle wasn't needed. Kill lands, but the
    # rifle slot survives so the player keeps it for a future round.
    target = PlayerState(
        user_id=10, first_name="Civ", join_order=1, role="citizen", team=Team.CITIZENS
    )
    don = PlayerState(user_id=20, first_name="Don", join_order=2, role="don", team=Team.MAFIA)
    actions = [
        NightAction(actor_id=20, role="don", action_type="kill", target_id=10, used_item="rifle")
    ]
    state = _state_with([target, don], actions)

    outcome = ActionResolver().resolve(state)
    assert outcome.deaths == [10]
    assert outcome.rifles_consumed == []


def test_killer_no_longer_pierces_shield():
    # Killer (Ninza) used to pierce shield intrinsically. Per the new
    # spec, only the rifle pierces shields — Killer just bypasses the
    # doctor heal. So a shield should still save against Killer when
    # rifle isn't involved.
    target = PlayerState(
        user_id=10,
        first_name="Civ",
        join_order=1,
        role="citizen",
        team=Team.CITIZENS,
        items_active=["shield"],
    )
    killer = PlayerState(
        user_id=20, first_name="Ninza", join_order=2, role="killer", team=Team.MAFIA
    )
    actions = [NightAction(actor_id=20, role="killer", action_type="kill", target_id=10)]
    state = _state_with([target, killer], actions)

    outcome = ActionResolver().resolve(state)
    assert outcome.deaths == []
    assert len(outcome.shield_saves) == 1
    assert outcome.shield_saves[0].item == "shield"


def test_killer_still_pierces_doctor_heal():
    # Killer's intrinsic ability: doctor cannot save the victim.
    # Shield isn't present here, so the kill goes through.
    target = PlayerState(
        user_id=10, first_name="Civ", join_order=1, role="citizen", team=Team.CITIZENS
    )
    killer = PlayerState(
        user_id=20, first_name="Ninza", join_order=2, role="killer", team=Team.MAFIA
    )
    doctor = PlayerState(
        user_id=30, first_name="Doc", join_order=3, role="doctor", team=Team.CITIZENS
    )
    actions = [
        NightAction(actor_id=20, role="killer", action_type="kill", target_id=10),
        NightAction(actor_id=30, role="doctor", action_type="heal", target_id=10),
    ]
    state = _state_with([target, killer, doctor], actions)

    outcome = ActionResolver().resolve(state)
    assert outcome.deaths == [10]
    # Doctor visit is logged but `saved=False`.
    saves_for_target = [r for r in outcome.doctor_results if r.target_id == 10]
    assert any(not r.saved for r in saves_for_target)


def test_hooker_cannot_sleep_killer():
    # Killer (Ninza) is immune to the Hooker just like premium players.
    # The visit is recorded with `blocked=True` so the Hooker gets
    # confirmation feedback, but the target isn't added to `sleeping`.
    killer = PlayerState(
        user_id=10, first_name="Ninza", join_order=1, role="killer", team=Team.MAFIA
    )
    hooker = PlayerState(
        user_id=20, first_name="Kez", join_order=2, role="hooker", team=Team.CITIZENS
    )
    actions = [NightAction(actor_id=20, role="hooker", action_type="sleep", target_id=10)]
    state = _state_with([killer, hooker], actions)

    outcome = ActionResolver().resolve(state)
    assert 10 not in outcome.sleeping
    assert len(outcome.hooker_results) == 1
    assert outcome.hooker_results[0].blocked is True


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


# === Mafia collusion (Don + Mafia share one weighted kill) ===


def _civ(uid: int, name: str = "Civ", **extra) -> PlayerState:
    return PlayerState(
        user_id=uid,
        first_name=name,
        join_order=uid,
        role="citizen",
        team=Team.CITIZENS,
        **extra,
    )


def _don(uid: int) -> PlayerState:
    return PlayerState(user_id=uid, first_name="Don", join_order=uid, role="don", team=Team.MAFIA)


def _mafia(uid: int, name: str = "Maf") -> PlayerState:
    return PlayerState(user_id=uid, first_name=name, join_order=uid, role="mafia", team=Team.MAFIA)


def test_don_alone_kill_lands_on_picked_target():
    target = _civ(10)
    don = _don(20)
    actions = [NightAction(actor_id=20, role="don", action_type="kill", target_id=10)]
    state = _state_with([target, don], actions)

    outcome = ActionResolver().resolve(state)

    assert outcome.deaths == [10]
    assert outcome.mafia_no_consensus is False


def test_don_pick_outweighs_two_mafia():
    """Don picks B (2.5), 2 Mafia pick A (2.0) → B dies."""
    a = _civ(10, "A")
    b = _civ(11, "B")
    don = _don(20)
    m1 = _mafia(21, "M1")
    m2 = _mafia(22, "M2")
    actions = [
        NightAction(actor_id=20, role="don", action_type="kill", target_id=11),
        NightAction(actor_id=21, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=22, role="mafia", action_type="kill", target_id=10),
    ]
    state = _state_with([a, b, don, m1, m2], actions)

    outcome = ActionResolver().resolve(state)

    assert outcome.deaths == [11]
    assert outcome.mafia_no_consensus is False


def test_three_mafia_outweigh_don():
    """3 Mafia pick A (3.0), Don picks B (2.5) → A dies."""
    a = _civ(10, "A")
    b = _civ(11, "B")
    don = _don(20)
    m1 = _mafia(21, "M1")
    m2 = _mafia(22, "M2")
    m3 = _mafia(23, "M3")
    actions = [
        NightAction(actor_id=20, role="don", action_type="kill", target_id=11),
        NightAction(actor_id=21, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=22, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=23, role="mafia", action_type="kill", target_id=10),
    ]
    state = _state_with([a, b, don, m1, m2, m3], actions)

    outcome = ActionResolver().resolve(state)

    assert outcome.deaths == [10]
    assert outcome.mafia_no_consensus is False


def test_mafia_split_1_1_no_consensus_when_don_abstains():
    """Don submits no action; 2 Mafia split 1:1 → tie, nobody dies."""
    a = _civ(10, "A")
    b = _civ(11, "B")
    don = _don(20)
    m1 = _mafia(21, "M1")
    m2 = _mafia(22, "M2")
    actions = [
        NightAction(actor_id=21, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=22, role="mafia", action_type="kill", target_id=11),
    ]
    state = _state_with([a, b, don, m1, m2], actions)

    outcome = ActionResolver().resolve(state)

    assert outcome.deaths == []
    assert outcome.mafia_no_consensus is True


def test_mafia_split_2_2_no_consensus_when_don_abstains():
    """Don submits no action; 2+2 Mafia split → tie, nobody dies."""
    a = _civ(10, "A")
    b = _civ(11, "B")
    don = _don(20)
    m1 = _mafia(21, "M1")
    m2 = _mafia(22, "M2")
    m3 = _mafia(23, "M3")
    m4 = _mafia(24, "M4")
    actions = [
        NightAction(actor_id=21, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=22, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=23, role="mafia", action_type="kill", target_id=11),
        NightAction(actor_id=24, role="mafia", action_type="kill", target_id=11),
    ]
    state = _state_with([a, b, don, m1, m2, m3, m4], actions)

    outcome = ActionResolver().resolve(state)

    assert outcome.deaths == []
    assert outcome.mafia_no_consensus is True


def test_don_breaks_tie_when_he_picks_one_side():
    """Tie between Mafia votes broken by Don joining one side."""
    a = _civ(10, "A")
    b = _civ(11, "B")
    don = _don(20)
    m1 = _mafia(21, "M1")
    m2 = _mafia(22, "M2")
    actions = [
        NightAction(actor_id=20, role="don", action_type="kill", target_id=10),
        NightAction(actor_id=21, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=22, role="mafia", action_type="kill", target_id=11),
    ]
    state = _state_with([a, b, don, m1, m2], actions)

    outcome = ActionResolver().resolve(state)

    # A: 2.5 (don) + 1 (m1) = 3.5; B: 1 (m2). A dies.
    assert outcome.deaths == [10]
    assert outcome.mafia_no_consensus is False


def test_killer_kill_independent_of_mafia_consensus():
    """Killer (Ninza) kills alongside mafia, on his own target, even when
    mafia ties — he is NOT part of the team vote."""
    a = _civ(10, "A")
    b = _civ(11, "B")
    c = _civ(12, "C")
    don = _don(20)
    m1 = _mafia(21, "M1")
    m2 = _mafia(22, "M2")
    killer = PlayerState(
        user_id=30, first_name="Ninza", join_order=30, role="killer", team=Team.MAFIA
    )
    actions = [
        NightAction(actor_id=21, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=22, role="mafia", action_type="kill", target_id=11),
        NightAction(actor_id=30, role="killer", action_type="kill", target_id=12),
    ]
    state = _state_with([a, b, c, don, m1, m2, killer], actions)

    outcome = ActionResolver().resolve(state)

    # Mafia tie → no mafia kill. Killer kills C independently.
    assert outcome.deaths == [12]
    assert outcome.mafia_no_consensus is True


def test_don_rifle_only_consumed_if_his_target_wins():
    """Don votes for B with rifle, but 3 Mafia outvote on A → team kills A,
    Don's rifle was not fired and must NOT be consumed."""
    a = _civ(10, "A")
    b = _civ(11, "B")
    don = _don(20)
    m1 = _mafia(21, "M1")
    m2 = _mafia(22, "M2")
    m3 = _mafia(23, "M3")
    actions = [
        NightAction(actor_id=20, role="don", action_type="kill", target_id=11, used_item="rifle"),
        NightAction(actor_id=21, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=22, role="mafia", action_type="kill", target_id=10),
        NightAction(actor_id=23, role="mafia", action_type="kill", target_id=10),
    ]
    state = _state_with([a, b, don, m1, m2, m3], actions)

    outcome = ActionResolver().resolve(state)

    assert outcome.deaths == [10]
    # Don's rifle is attached to B (loser), so no rifle consumption.
    assert outcome.rifles_consumed == []
