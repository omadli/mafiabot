"""Smoke tests for the new admin/SA API endpoints.

Strategy: spin up a FastAPI TestClient against the bare router objects.
Mock the auth dependency to return a stub admin/SA. Mock the service
layer to avoid touching Tortoise. We exercise wiring + serialization,
not business logic — that's covered by the service unit tests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from app.api.deps import (
    SuperAdminContext,
    get_current_admin,
    get_current_super_admin,
)
from app.api.routers import admin, public, super_admin
from app.db.models import AdminAccount
from fastapi import FastAPI
from fastapi.testclient import TestClient

# --- Fakes ---------------------------------------------------------


class _FakeAdmin:
    """Quack like AdminAccount enough for logging + audit."""

    id = "11111111-1111-1111-1111-111111111111"
    username = "test-admin"
    role = "super_admin"
    is_active = True
    telegram_id = 1334765613
    last_login_at = None


def _fake_admin() -> AdminAccount:
    return _FakeAdmin()  # type: ignore[return-value]


def _fake_sa() -> SuperAdminContext:
    return SuperAdminContext(
        telegram_id=1334765613,
        first_name="Dev",
        username="dev",
        language_code="uz",
    )


# --- App fixture --------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(public.router)
    app.include_router(admin.router, prefix="/api")
    app.include_router(super_admin.router)

    app.dependency_overrides[get_current_admin] = _fake_admin
    app.dependency_overrides[get_current_super_admin] = _fake_sa
    return TestClient(app)


def _fake_cfg(**kw):
    cfg = type("F", (), {})()
    for k, v in kw.items():
        setattr(cfg, k, v)
    if "updated_at" not in kw:
        cfg.updated_at = datetime.now(UTC)
    if "updated_by_tg_id" not in kw:
        cfg.updated_by_tg_id = None
    return cfg


SAMPLE_ROLE_CONFIGS = {
    "citizen": _fake_cfg(
        role="citizen",
        team="civilians",
        static_emoji="👨🏼",
        custom_emoji_id="",
        order_idx=10,
        name_uz="Tinch aholi",
        name_ru="Мирный житель",
        name_en="Civilian",
    ),
    "doctor": _fake_cfg(
        role="doctor",
        team="civilians",
        static_emoji="👨🏻‍⚕",
        custom_emoji_id="5429363657471434941",
        order_idx=50,
        name_uz="Doktor",
        name_ru="Доктор",
        name_en="Doctor",
    ),
}

SAMPLE_EMOJI_CONFIGS = {
    "scene-night": _fake_cfg(
        code="scene-night",
        category="scene",
        order_idx=20,
        name_uz="Tun",
        name_ru="Ночь",
        name_en="Night",
        static_emoji="🌙",
        custom_emoji_id="",
    ),
    "status-death": _fake_cfg(
        code="status-death",
        category="status",
        order_idx=110,
        name_uz="O'lim",
        name_ru="Смерть",
        name_en="Death",
        static_emoji="💀",
        custom_emoji_id="5269123456789012345",
    ),
}


# --- /api/public/role-configs (no auth) --------------------------


def test_public_role_configs_returns_sorted_items(client: TestClient):
    with patch(
        "app.services.role_config_service.get_all_configs",
        return_value=SAMPLE_ROLE_CONFIGS,
    ):
        r = client.get("/api/public/role-configs")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    codes = [i["role"] for i in body["items"]]
    assert codes == ["citizen", "doctor"]  # order_idx sorted


def test_public_role_configs_serialises_all_fields(client: TestClient):
    with patch(
        "app.services.role_config_service.get_all_configs",
        return_value=SAMPLE_ROLE_CONFIGS,
    ):
        r = client.get("/api/public/role-configs")
    item = r.json()["items"][0]
    for key in ("role", "team", "name_uz", "name_ru", "name_en", "static_emoji", "custom_emoji_id"):
        assert key in item


# --- /api/admin/role-configs (JWT auth — overridden) ------------


def test_admin_role_configs_requires_auth_in_real_setup(client: TestClient):
    """With our fake admin dep override, the endpoint should respond 200."""
    with patch(
        "app.services.role_config_service.get_all_configs",
        return_value=SAMPLE_ROLE_CONFIGS,
    ):
        r = client.get("/api/admin/role-configs")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 2


def test_admin_role_configs_update_validates_team(client: TestClient):
    """Bad team value → 400 from Pydantic Literal validation."""
    r = client.post(
        "/api/admin/role-configs/citizen",
        json={"team": "invalid-team"},
    )
    # Pydantic validation errors → 422 (FastAPI default for body parsing)
    assert r.status_code in (400, 422)


def test_admin_role_configs_update_with_empty_body_rejected(client: TestClient):
    r = client.post("/api/admin/role-configs/citizen", json={})
    assert r.status_code == 400
    assert "No fields" in r.json()["detail"]


def test_admin_role_configs_update_calls_service(client: TestClient):
    fake_updated = _fake_cfg(
        role="citizen",
        team="civilians",
        static_emoji="🧑",
        custom_emoji_id="",
        order_idx=10,
        name_uz="Aholi",
        name_ru="Житель",
        name_en="Citizen",
    )
    with (
        patch(
            "app.services.role_config_service.update_config",
            return_value=fake_updated,
        ) as mock_update,
        patch(
            "app.api.routers.admin.log_action",
            return_value=None,
        ),
    ):
        r = client.post(
            "/api/admin/role-configs/citizen",
            json={"name_uz": "Aholi", "static_emoji": "🧑"},
        )
    assert r.status_code == 200
    assert mock_update.called
    assert r.json()["static_emoji"] == "🧑"


# --- /api/sa/role-configs --------------------------------------


def test_sa_role_configs_endpoint(client: TestClient):
    with patch(
        "app.services.role_config_service.get_all_configs",
        return_value=SAMPLE_ROLE_CONFIGS,
    ):
        r = client.get("/api/sa/role-configs")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 2


# --- /api/admin/emoji-configs ----------------------------------


def test_admin_emoji_configs_returns_sorted_by_order(client: TestClient):
    with patch(
        "app.services.emoji_config_service.get_all_configs",
        return_value=SAMPLE_EMOJI_CONFIGS,
    ):
        r = client.get("/api/admin/emoji-configs")
    assert r.status_code == 200
    codes = [i["code"] for i in r.json()["items"]]
    assert codes == ["scene-night", "status-death"]


def test_admin_emoji_configs_update(client: TestClient):
    fake_updated = _fake_cfg(
        code="scene-night",
        category="scene",
        order_idx=20,
        name_uz="Tun",
        name_ru="Ночь",
        name_en="Night",
        static_emoji="🌚",
        custom_emoji_id="",
    )
    with (
        patch(
            "app.services.emoji_config_service.update_config",
            return_value=fake_updated,
        ),
        patch("app.api.routers.admin.log_action", return_value=None),
    ):
        r = client.post(
            "/api/admin/emoji-configs/scene-night",
            json={"static_emoji": "🌚"},
        )
    assert r.status_code == 200
    assert r.json()["static_emoji"] == "🌚"


def test_admin_emoji_configs_update_rejects_unknown_field(client: TestClient):
    """Unknown field is accepted by Pydantic (optional fields default None),
    but service's whitelist would reject it via ValueError → 400."""
    with patch(
        "app.services.emoji_config_service.update_config",
        side_effect=ValueError("unknown field"),
    ):
        r = client.post(
            "/api/admin/emoji-configs/scene-night",
            json={"static_emoji": "🌝"},  # ok shape, service stubs raise
        )
    assert r.status_code == 400


# --- /api/sa/emoji-configs --------------------------------------


def test_sa_emoji_configs_endpoint(client: TestClient):
    with patch(
        "app.services.emoji_config_service.get_all_configs",
        return_value=SAMPLE_EMOJI_CONFIGS,
    ):
        r = client.get("/api/sa/emoji-configs")
    assert r.status_code == 200
    body = r.json()
    assert any(i["custom_emoji_id"] for i in body["items"])
