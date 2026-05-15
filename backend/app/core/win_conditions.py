"""Win condition checks — called after each phase.

Tomon yoki Singleton g'olib bo'lganini tekshiradi.
"""

from app.core.state import GameState, Team


def check_winner(state: GameState) -> Team | None:
    """Return winning team if game has ended, else None.

    Singleton victories also reported as Team.SINGLETON. Specific singleton role
    that won is encoded in state.winner_user_ids (only those user_ids).
    """
    # Guard: no players → no winner. Avoids the 0>=0 case wrongly returning Mafia
    # for cancelled games where registration timed out.
    if not state.players:
        return None

    alive = state.alive_players()
    mafia_alive = [p for p in alive if p.team == Team.MAFIA]
    citizens_alive = [p for p in alive if p.team == Team.CITIZENS]

    # === Singleton victories ===
    # 1. Maniac alone — only maniac alive (or maniac + 1 powerless person)
    maniacs = state.alive_by_role("maniac")
    if maniacs and len(alive) <= 1:
        # Only maniac left → he wins
        return Team.SINGLETON

    # 2. Crook (Aferist) — survived to end (game otherwise ended)
    # Handled when game ends via other win — flagged as singleton win then.

    # 3. Mage (Sehrgar) — survived to end
    # Same as crook.

    # 4. Suicide — was hanged (not alive); win flagged elsewhere
    suicide_won = any(
        p.role == "suicide" and not p.alive and p.died_at_phase == "voting" for p in state.players
    )
    if suicide_won and not _game_can_continue(state):
        return Team.SINGLETON

    # 5. Snitch — has revealed at least 1 (and survived) — flag elsewhere
    # 6. Arsonist — killed >=3 (queue + chain)
    arsonist = next((p for p in state.players if p.role == "arsonist"), None)
    if arsonist and arsonist.extra.get("arsonist_triggered"):
        kills = len(arsonist.extra.get("target_queue", []))
        if kills >= 3:
            return Team.SINGLETON

    # Singletons (Mage, Crook, Werewolf, ...) outlived both teams.
    # Without this guard, the team fallback below would credit Mafia for
    # 0 >= 0 — a mage-alone-alive game would wrongly report Mafia victory.
    if not mafia_alive and not citizens_alive and alive:
        return Team.SINGLETON

    # === Citizens vs Mafia ===
    if not mafia_alive and citizens_alive:
        return Team.CITIZENS

    if len(mafia_alive) >= len(citizens_alive):
        return Team.MAFIA

    return None


def _game_can_continue(state: GameState) -> bool:
    """Check if game has enough players + balance to continue."""
    alive = state.alive_players()
    return len(alive) >= 3


def winner_user_ids(state: GameState, winner: Team) -> list[int]:
    """User IDs who win.

    For SINGLETON: include only specific singleton role(s) that satisfied their win condition.
    For team wins: ONLY members of the winning team who are still ALIVE — dead
    players are passengers, not winners. (Reference parity with @MafiaAzBot.)
    """
    if winner != Team.SINGLETON:
        return [p.user_id for p in state.players if p.team == winner and p.alive]

    # Determine which singleton(s) actually won
    winners: list[int] = []

    # Maniac — last alive
    alive = state.alive_players()
    maniacs = state.alive_by_role("maniac")
    if maniacs and len(alive) <= 1:
        winners.extend(p.user_id for p in maniacs)

    # Arsonist — 3+ kills triggered
    for p in state.players:
        if (
            p.role == "arsonist"
            and p.extra.get("arsonist_triggered")
            and len(p.extra.get("target_queue", [])) >= 3
        ):
            winners.append(p.user_id)

    # Suicide — hanged
    for p in state.players:
        if p.role == "suicide" and not p.alive and p.died_at_phase == "voting":
            winners.append(p.user_id)

    # Mage / Crook — survived to end
    if not _game_can_continue(state) or len(alive) <= 2:
        for p in state.players:
            if p.role in ("mage", "crook") and p.alive:
                winners.append(p.user_id)

    # Snitch — revealed someone (and alive)
    for p in state.players:
        if p.role == "snitch" and p.alive and p.extra.get("snitch_revealed_count", 0) >= 1:
            winners.append(p.user_id)

    # Kamikaze — took mafia member
    for p in state.players:
        if p.role == "kamikaze" and not p.alive:
            took = p.extra.get("kamikaze_took_role")
            if took in ("don", "mafia", "lawyer", "journalist", "killer", "maniac"):
                winners.append(p.user_id)

    # Werewolf — survived to end
    if not _game_can_continue(state):
        for p in state.players:
            if p.role == "werewolf" and p.alive:
                winners.append(p.user_id)

    return list(set(winners))
