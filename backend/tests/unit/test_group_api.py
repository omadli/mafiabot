"""Smoke tests for `/api/group/*` — the Telegram WebApp surface.

Strategy mirrors `test_api_endpoints.py`: spin up a FastAPI TestClient
against the bare router, override the auth dependency to bypass
initData + admin checks, and mock Tortoise queries via `unittest.mock`.

These tests exist to catch wiring/serialisation regressions on the
endpoints the WebApp's group-admin pages call. They do NOT exercise
business logic — that's covered by the service-layer tests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.api.routers import group as group_router
from app.api.routers.group import WebAppAuthData, require_group_admin, validate_webapp
from fastapi import FastAPI
from fastapi.testclient import TestClient

GROUP_ID = -1001234567890
USER_ID = 4242424242


def _fake_auth() -> WebAppAuthData:
    return WebAppAuthData(user_id=USER_ID, chat_id=GROUP_ID)


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(group_router.router, prefix="/api")
    app.dependency_overrides[validate_webapp] = _fake_auth
    app.dependency_overrides[require_group_admin] = _fake_auth
    return TestClient(app)


# === Fake DB rows ===


class _FakeGroup:
    """Minimal `Group`-shaped object."""

    def __init__(self, *, gid: int = GROUP_ID, title: str = "Test Group") -> None:
        self.id = gid
        self.title = title


class _FakeSettings:
    """Minimal `GroupSettings`-shaped object."""

    def __init__(self) -> None:
        self.group_id = GROUP_ID
        self.language = "uz"
        self.roles = {"citizen": True, "don": True}
        self.timings = {"night": 60, "day": 30}
        self.silence = {"dead_players": True}
        self.items_allowed = {"shield": True}
        self.role_distribution: dict = {}
        self.afk = {"skip_phases_before_kick": 2}
        self.permissions = {"who_can_register": "all", "allow_leave": True}
        self.gameplay = {"mafia_ratio": "low", "min_players": 4}
        self.display = {"show_role_emojis": True}
        self.messages: dict = {}
        self.atmosphere_media: dict = {}


class _FakeGame:
    """Minimal `Game`-shaped object the history endpoint reads."""

    def __init__(
        self,
        *,
        players_history: list[dict],
        winner_team: object | None = None,
        bounty: int | None = None,
    ) -> None:
        self.id = uuid4()
        self.status = "finished"
        self.started_at = datetime(2026, 5, 30, 10, 0, tzinfo=UTC)
        self.finished_at = datetime(2026, 5, 30, 10, 18, tzinfo=UTC)
        self.winner_team = winner_team
        self.bounty_per_winner = bounty
        self.history = {"players": players_history}


# === GET /group/{id}/settings — public ===


def test_settings_get_returns_shape(client: TestClient):
    fake_group = _FakeGroup()
    fake_group.settings = _FakeSettings()  # type: ignore[attr-defined]
    mock = AsyncMock(return_value=fake_group)
    with patch.object(group_router.Group, "get_or_none", return_value=_AwaitableGet(fake_group)):
        r = client.get(f"/api/group/{GROUP_ID}/settings")
    assert r.status_code == 200, r.text
    body = r.json()
    for key in (
        "group_id",
        "title",
        "language",
        "roles",
        "timings",
        "silence",
        "items_allowed",
        "role_distribution",
        "afk",
        "permissions",
        "gameplay",
        "display",
        "messages",
        "atmosphere_media",
    ):
        assert key in body, f"missing key {key!r}"
    assert body["group_id"] == GROUP_ID
    assert body["language"] == "uz"
    _ = mock  # touch to satisfy any lint


def test_settings_get_404_when_group_missing(client: TestClient):
    with patch.object(group_router.Group, "get_or_none", return_value=_AwaitableGet(None)):
        r = client.get(f"/api/group/{GROUP_ID}/settings")
    assert r.status_code == 404


# === POST /group/{id}/settings — section accept/reject ===


@pytest.mark.parametrize(
    "section,value",
    [
        ("roles", {"don": True, "mafia": False}),
        ("timings", {"night": 75, "day": 45}),
        ("silence", {"dead_players": True}),
        ("items_allowed", {"shield": True, "rifle": False}),
        (
            "role_distribution",
            {
                "8": [
                    "don",
                    "detective",
                    "doctor",
                    "citizen",
                    "citizen",
                    "citizen",
                    "citizen",
                    "citizen",
                ]
            },
        ),
        ("afk", {"skip_phases_before_kick": 3}),
        ("permissions", {"who_can_register": "admins", "allow_leave": False}),
        ("gameplay", {"mafia_ratio": "high", "min_players": 5, "max_players": 25}),
        ("display", {"show_role_emojis": False}),
        ("language", "ru"),
    ],
)
def test_settings_post_accepts_each_section(client: TestClient, section: str, value):
    """Every section name the regex allows must round-trip cleanly with a
    mixed-type value (strings, booleans, numbers nested in dicts)."""
    fake_group = _FakeGroup()
    fake_settings = _FakeSettings()
    with (
        patch.object(group_router.Group, "get_or_none", return_value=_AwaitableGet(fake_group)),
        patch(
            "app.db.models.GroupSettings.get_or_none",
            return_value=_AwaitableGet(fake_settings),
        ),
        patch("app.services.group_settings_helper.save_settings_fields", new=AsyncMock()),
        patch("app.api.routers.group.log_action", new=AsyncMock()),
    ):
        r = client.post(
            f"/api/group/{GROUP_ID}/settings",
            json={"section": section, "value": value},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["section"] == section


def test_settings_post_rejects_unknown_section(client: TestClient):
    r = client.post(
        f"/api/group/{GROUP_ID}/settings",
        json={"section": "evil_section", "value": {}},
    )
    assert r.status_code == 422


def test_settings_post_rejects_chat_id_mismatch(client: TestClient):
    r = client.post(
        f"/api/group/{GROUP_ID + 1}/settings",
        json={"section": "roles", "value": {"don": True}},
    )
    assert r.status_code == 403


def test_settings_post_rejects_bad_language(client: TestClient):
    fake_group = _FakeGroup()
    fake_settings = _FakeSettings()
    with (
        patch.object(group_router.Group, "get_or_none", return_value=_AwaitableGet(fake_group)),
        patch(
            "app.db.models.GroupSettings.get_or_none",
            return_value=_AwaitableGet(fake_settings),
        ),
    ):
        r = client.post(
            f"/api/group/{GROUP_ID}/settings",
            json={"section": "language", "value": "too-long-code-here"},
        )
    assert r.status_code == 400


# === GET /group/{id}/history — alive count regression ===


def test_history_alive_count_uses_inline_player_flags(client: TestClient):
    """Regression: history endpoint must count survivors via the inline
    `alive=True` flag on each player snapshot (NOT a non-existent
    `final_alive` array — `to_history_dict()` doesn't emit one)."""

    players = [
        {"user_id": 1, "first_name": "A", "alive": True, "role": "citizen"},
        {"user_id": 2, "first_name": "B", "alive": False, "role": "don"},
        {"user_id": 3, "first_name": "C", "alive": True, "role": "doctor"},
        {"user_id": 4, "first_name": "D", "alive": False, "role": "mafia"},
        {"user_id": 5, "first_name": "E", "alive": True, "role": "detective"},
    ]
    game = _FakeGame(players_history=players)

    with patch(
        "app.db.models.Game.filter",
        return_value=_FakeQS(items=[game], total=1),
    ):
        r = client.get(f"/api/group/{GROUP_ID}/history")

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["player_count"] == 5
    assert item["alive_at_end"] == 3, item


def test_history_returns_empty_when_no_games(client: TestClient):
    with patch(
        "app.db.models.Game.filter",
        return_value=_FakeQS(items=[], total=0),
    ):
        r = client.get(f"/api/group/{GROUP_ID}/history")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0


# === Async-await test helpers ===


class _AwaitableGet:
    """Stand-in for the chainable Tortoise QuerySet `Group.get_or_none(id=x).prefetch_related(...)`.

    The endpoint either awaits the result directly (`await Group.get_or_none(id=x)`)
    or chains a `.prefetch_related(...)` first. We need the same instance
    to be returned from both shapes.
    """

    def __init__(self, value):  # type: ignore[no-untyped-def]
        self._value = value

    def prefetch_related(self, *_a, **_kw):  # type: ignore[no-untyped-def]
        return self

    def __await__(self):  # type: ignore[no-untyped-def]
        async def _coro():
            return self._value

        return _coro().__await__()


class _FakeQS:
    """Tortoise-shaped QuerySet that supports `.filter().count() / .order_by().offset().limit().all()`."""

    def __init__(self, *, items: list, total: int) -> None:
        self._items = items
        self._total = total

    def filter(self, **_kw):  # type: ignore[no-untyped-def]
        return self

    def order_by(self, *_a, **_kw):  # type: ignore[no-untyped-def]
        return self

    def offset(self, *_a, **_kw):  # type: ignore[no-untyped-def]
        return self

    def limit(self, *_a, **_kw):  # type: ignore[no-untyped-def]
        return self

    async def count(self) -> int:
        return self._total

    def all(self):  # type: ignore[no-untyped-def]
        async def _coro():
            return self._items

        return _coro()

    def __await__(self):  # type: ignore[no-untyped-def]
        async def _coro():
            return self._items

        return _coro().__await__()
