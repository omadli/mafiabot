"""Tests for role_config_service — focus on sync helpers + override merging
that can be exercised without spinning up the DB.

The DB-backed code paths (get_all_configs / update_config) are covered by
integration tests run against a live SQLite under tests/integration when
the suite is wired up; here we hit only the in-memory cache path and the
i18n translator integration.
"""

from __future__ import annotations

import pytest
from app.services import role_config_service


class _FakeCfg:
    """Lightweight stand-in for a RoleConfig row (no DB needed)."""

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


@pytest.fixture(autouse=True)
def _warm_cache():
    """Populate role_config_service cache with a few fake roles."""
    role_config_service._cache["configs"] = {
        "citizen": _FakeCfg(
            role="citizen",
            team="civilians",
            static_emoji="👨🏼",
            custom_emoji_id="",
            order_idx=10,
            name_uz="Tinch aholi",
            name_ru="Мирный житель",
            name_en="Civilian",
        ),
        "doctor": _FakeCfg(
            role="doctor",
            team="civilians",
            static_emoji="👨🏻‍⚕",
            custom_emoji_id="5429363657471434941",
            order_idx=50,
            name_uz="Doktor",
            name_ru="Доктор",
            name_en="Doctor",
        ),
        "snitch": _FakeCfg(
            role="snitch",
            team="singletons",
            static_emoji="🤓",
            custom_emoji_id="5370856771151730818",
            order_idx=270,
            name_uz="Sotqin",
            name_ru="Предатель",
            name_en="Snitch",
        ),
    }
    role_config_service._cache["ts"] = 9_999_999_999.0
    yield
    role_config_service.invalidate_cache()


def test_role_label_sync_returns_none_when_cold():
    role_config_service.invalidate_cache()
    assert role_config_service.role_label_sync("citizen", "uz") is None


def test_role_label_sync_static_only_role():
    s = role_config_service.role_label_sync("citizen", "uz")
    assert s == "👨🏼 Tinch aholi"


def test_role_label_sync_custom_emoji_wraps_in_tg_emoji_tag():
    s = role_config_service.role_label_sync("doctor", "uz")
    assert s == '<tg-emoji emoji-id="5429363657471434941">👨🏻‍⚕</tg-emoji> Doktor'


def test_role_label_sync_picks_localised_name():
    assert role_config_service.role_label_sync("snitch", "ru").endswith(" Предатель")
    assert role_config_service.role_label_sync("snitch", "en").endswith(" Snitch")
    assert role_config_service.role_label_sync("snitch", "uz").endswith(" Sotqin")


def test_role_label_sync_unknown_locale_falls_back_to_uz():
    s = role_config_service.role_label_sync("citizen", "fr")
    assert s == "👨🏼 Tinch aholi"


def test_role_label_sync_unknown_role_returns_none():
    assert role_config_service.role_label_sync("nonexistent", "uz") is None


def test_override_via_list_form():
    overrides = {"citizen": ["999", "🧑"]}
    s = role_config_service.role_label_sync("citizen", "uz", overrides=overrides)
    assert s == '<tg-emoji emoji-id="999">🧑</tg-emoji> Tinch aholi'


def test_override_via_dict_form_with_name():
    overrides = {
        "doctor": {"custom_id": "", "fallback": "🩺", "name_uz": "Shifokor"},
    }
    s = role_config_service.role_label_sync("doctor", "uz", overrides=overrides)
    assert s == "🩺 Shifokor"


def test_override_clears_custom_id_via_empty_string():
    overrides = {"doctor": {"custom_id": "", "fallback": "👨‍⚕"}}
    s = role_config_service.role_label_sync("doctor", "uz", overrides=overrides)
    assert s == "👨‍⚕ Doktor"
    # No tg-emoji wrapper any more
    assert "<tg-emoji" not in s


def test_malformed_override_falls_back_to_default():
    overrides = {"citizen": "not an override"}
    s = role_config_service.role_label_sync("citizen", "uz", overrides=overrides)
    assert s == "👨🏼 Tinch aholi"


def test_coerce_override_handles_empty_inputs():
    assert role_config_service._coerce_override(None) is None
    assert role_config_service._coerce_override([]) is None
    assert role_config_service._coerce_override(["a"]) is None
    assert role_config_service._coerce_override({}) is None
    # missing fallback
    assert role_config_service._coerce_override({"custom_id": "x"}) is None


def test_editable_fields_set():
    # Whitelist must include every column an admin can edit in the dashboard
    assert (
        frozenset(
            {
                "team",
                "name_uz",
                "name_ru",
                "name_en",
                "static_emoji",
                "custom_emoji_id",
                "order_idx",
            }
        )
        == role_config_service.EDITABLE_FIELDS
    )


# --- i18n translator integration -----------------------------------


def test_translator_dispatches_role_keys_to_role_config_service():
    from app.services.i18n_service import get_translator

    _ = get_translator("uz")
    assert _("role-citizen") == "👨🏼 Tinch aholi"
    assert _("role-doctor").endswith(" Doktor")
    assert _("role-doctor").startswith('<tg-emoji emoji-id="5429363657471434941">')


def test_translator_role_desc_keys_still_go_to_fluent():
    # role-desc-* must NOT short-circuit (only role-* without -desc-)
    from app.services.i18n_service import get_translator

    _ = get_translator("uz")
    # role-desc-citizen exists in .ftl; we just check no crash + non-empty
    out = _("role-desc-citizen")
    assert isinstance(out, str) and len(out) > 0


def test_translator_unknown_role_falls_through_to_fluent_lookup():
    # If role-config cache misses, the translator should fall through to
    # fluent. Even if fluent has no key it just returns the key string back.
    from app.services.i18n_service import get_translator

    _ = get_translator("uz")
    # This slug isn't in defaults — should attempt fluent and likely get key back
    result = _("role-aliens")
    assert isinstance(result, str)


def test_translator_overrides_apply_per_group():
    from app.services.i18n_service import get_translator

    overrides = {"citizen": ["7777", "🧑‍🦱"]}
    _ = get_translator("uz", role_overrides=overrides)
    s = _("role-citizen")
    assert "7777" in s
    assert " Tinch aholi" in s  # name still comes from global config
