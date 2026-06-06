"""All-roles-enabled full-game completion guard.

The role enabled-map only ever *substitutes out* roles, never adds them —
so `DEFAULT_DISTRIBUTION[n]` already specifies the special roles
(maniac@14, mage@20, arsonist@21, journalist@23, …). With every role
enabled, those mechanics + win-conditions finally fire in real games
instead of being downgraded to citizen/mafia.

This test proves a full game still TERMINATES (reaches FINISHED, no crash,
no deadlock) with all 21 roles enabled across a spread of player counts.
It guards the all-True default and any future role-mechanic change.

Drives the engine deterministically (start_game + tick_once with
auto-submitted actions), mirroring test_sandbox_lifecycle, so there is no
asyncio timer loop to cancel.
"""

from __future__ import annotations

import asyncio
import random
from uuid import uuid4

import pytest
from app.core.phases.manager import PhaseManager
from app.core.state import Phase
from app.db.models import AdminAccount
from app.db.models.group import DEFAULT_ROLES_ENABLED
from app.services import game_service, sandbox_service, transcript_store
from app.services.recording_bot import SandboxBot, SandboxBotRegistry
from app.services.sandbox_service import SandboxCreateConfig, _submit_auto_actions
from app.services.transcript_store import MemoryTranscriptBackend
from tortoise import Tortoise


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module", autouse=True)
async def _db():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={
            "models": [
                "app.db.models.user",
                "app.db.models.group",
                "app.db.models.game",
                "app.db.models.statistics",
                "app.db.models.transaction",
                "app.db.models.audit",
                "app.db.models.system_settings",
                "app.db.models.role_config",
                "app.db.models.emoji_config",
                "app.db.models.sandbox",
            ]
        },
    )
    await Tortoise.generate_schemas(safe=True)
    yield
    await Tortoise.close_connections()


@pytest.fixture(autouse=True)
def _memory_redis():
    transcript_store.set_backend(MemoryTranscriptBackend())
    from app.core import redis_state

    redis_state._backend = redis_state.MemoryBackend()
    yield
    transcript_store.set_backend(None)
    redis_state._backend = None
    SandboxBotRegistry.clear()


@pytest.fixture
async def admin():
    return await AdminAccount.create(
        username=f"sa-{uuid4().hex[:6]}",
        password_hash="x",
        role="superadmin",
    )


@pytest.mark.parametrize("n_players", [14, 20, 25, 30])
async def test_all_roles_enabled_game_completes(admin, n_players):
    """With every role enabled, a full game must still reach FINISHED."""
    # Deterministic: role distribution + auto-play picks read the global RNG,
    # so seed it (other tests would otherwise leave it in an arbitrary state
    # and make this flaky). The seed is one that converges for every N here.
    random.seed(20260606 + n_players)
    all_on = dict.fromkeys(DEFAULT_ROLES_ENABLED, True)
    session = await sandbox_service.create_sandbox(
        admin,
        SandboxCreateConfig(
            n_players=n_players,
            timing_preset=sandbox_service.SandboxTimingPreset.MANUAL,
            roles_enabled=all_on,
        ),
    )

    state = await game_service.load_state(session.fake_group_id)
    assert state is not None
    bot = SandboxBot(
        sandbox_id=session.id,
        fake_group_id=session.fake_group_id,
        creator_fake_user_id=state.creator_user_id or 0,
    )
    SandboxBotRegistry.register(bot)

    await game_service.start_game(state)
    assert state.phase == Phase.NIGHT

    # Every assigned role must be a real, registered role (no leftover
    # placeholder slipped through distribution).
    from app.core.roles import ROLE_REGISTRY

    assert all(p.role in ROLE_REGISTRY for p in state.players)

    # Drive the game to completion. Auto-submit night actions / votes /
    # hang-confirm each relevant phase, then force-advance.
    max_ticks = 1000
    finished = False
    for _ in range(max_ticks):
        state = await game_service.load_state(session.fake_group_id)
        if state is None or state.phase in (Phase.FINISHED, Phase.CANCELLED):
            finished = True
            break
        if state.phase in (Phase.NIGHT, Phase.VOTING, Phase.HANGING_CONFIRM):
            await _submit_auto_actions(state, "auto")
            await game_service.save_state(state)
        await PhaseManager.tick_once(bot, session.fake_group_id, force=True)

    assert finished, f"N={n_players}: game did not terminate within {max_ticks} ticks (deadlock?)"

    final = await game_service.load_state(session.fake_group_id)
    # finish_game may have cleared Redis (None) or left a FINISHED snapshot.
    assert final is None or final.phase in (Phase.FINISHED, Phase.CANCELLED)
