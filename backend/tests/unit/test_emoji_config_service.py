"""Tests for emoji_config_service — sync cache helpers + override merging.

DB-free: we shove fake EmojiConfig objects directly into the module
cache. Integration with Tortoise is covered separately by API tests.
"""

from __future__ import annotations

import pytest
from app.services import emoji_config_service


class _FakeCfg:
    """Stand-in for an EmojiConfig row."""

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


@pytest.fixture(autouse=True)
def _warm_cache():
    """Inject a handful of fake configs spanning every category."""
    emoji_config_service._cache["configs"] = {
        "scene-night": _FakeCfg(
            code="scene-night",
            category="scene",
            order_idx=20,
            name_uz="Tun",
            name_ru="Ночь",
            name_en="Night",
            static_emoji="🌙",
            custom_emoji_id="",
        ),
        "scene-day": _FakeCfg(
            code="scene-day",
            category="scene",
            order_idx=30,
            name_uz="Kun",
            name_ru="День",
            name_en="Day",
            static_emoji="☀️",
            custom_emoji_id="",
        ),
        "status-death": _FakeCfg(
            code="status-death",
            category="status",
            order_idx=110,
            name_uz="O'lim",
            name_ru="Смерть",
            name_en="Death",
            static_emoji="💀",
            custom_emoji_id="5269123456789012345",
        ),
        "item-shield": _FakeCfg(
            code="item-shield",
            category="item",
            order_idx=210,
            name_uz="Qalqon",
            name_ru="Щит",
            name_en="Shield",
            static_emoji="🛡",
            custom_emoji_id="",
        ),
        "action-kill": _FakeCfg(
            code="action-kill",
            category="action",
            order_idx=310,
            name_uz="Hujum",
            name_ru="Атака",
            name_en="Attack",
            static_emoji="🔪",
            custom_emoji_id="",
        ),
        "currency-diamond": _FakeCfg(
            code="currency-diamond",
            category="currency",
            order_idx=410,
            name_uz="Olmos",
            name_ru="Алмаз",
            name_en="Diamond",
            static_emoji="💎",
            custom_emoji_id="",
        ),
    }
    emoji_config_service._cache["ts"] = 9_999_999_999.0
    yield
    emoji_config_service.invalidate_cache()


# --- Sync cache helper ---------------------------------------------


def test_emoji_html_sync_cold_cache_returns_none():
    emoji_config_service.invalidate_cache()
    assert emoji_config_service.emoji_html_sync("scene-night") is None


def test_emoji_html_sync_unknown_code_returns_none():
    assert emoji_config_service.emoji_html_sync("scene-doesnt-exist") is None


def test_emoji_html_sync_static_only():
    assert emoji_config_service.emoji_html_sync("scene-night") == "🌙"
    assert emoji_config_service.emoji_html_sync("scene-day") == "☀️"
    assert emoji_config_service.emoji_html_sync("item-shield") == "🛡"


def test_emoji_html_sync_custom_emoji_wraps_in_tg_emoji():
    s = emoji_config_service.emoji_html_sync("status-death")
    assert s == '<tg-emoji emoji-id="5269123456789012345">💀</tg-emoji>'


# --- Override formats ----------------------------------------------


def test_override_list_form_2_elements():
    s = emoji_config_service.emoji_html_sync(
        "scene-night", overrides={"scene-night": ["999", "🌑"]}
    )
    assert s == '<tg-emoji emoji-id="999">🌑</tg-emoji>'


def test_override_dict_form_with_custom_id_and_fallback():
    s = emoji_config_service.emoji_html_sync(
        "scene-night",
        overrides={"scene-night": {"custom_id": "888", "fallback": "🌜"}},
    )
    assert s == '<tg-emoji emoji-id="888">🌜</tg-emoji>'


def test_override_clears_custom_emoji_id_via_empty_string():
    """An override with empty custom_id should yield plain Unicode."""
    s = emoji_config_service.emoji_html_sync(
        "status-death",
        overrides={"status-death": {"custom_id": "", "fallback": "💀"}},
    )
    assert s == "💀"
    assert "<tg-emoji" not in s


def test_override_dict_uses_emoji_key_when_fallback_absent():
    s = emoji_config_service.emoji_html_sync(
        "scene-night",
        overrides={"scene-night": {"custom_id": "777", "emoji": "🌚"}},
    )
    assert s == '<tg-emoji emoji-id="777">🌚</tg-emoji>'


def test_malformed_override_falls_back_to_default():
    s = emoji_config_service.emoji_html_sync(
        "scene-night", overrides={"scene-night": "totally wrong"}
    )
    assert s == "🌙"


def test_override_with_no_fallback_falls_back_to_default():
    """An override without a fallback char is invalid — silently dropped."""
    s = emoji_config_service.emoji_html_sync(
        "scene-night",
        overrides={"scene-night": {"custom_id": "5"}},  # no fallback / emoji
    )
    assert s == "🌙"


def test_override_for_unrelated_code_doesnt_affect_target():
    s = emoji_config_service.emoji_html_sync("scene-night", overrides={"item-shield": ["1", "🛡"]})
    assert s == "🌙"


def test_override_empty_dict_is_ignored():
    assert emoji_config_service.emoji_html_sync("scene-night", overrides={}) == "🌙"


def test_override_none_is_ignored():
    assert emoji_config_service.emoji_html_sync("scene-night", overrides=None) == "🌙"


# --- _coerce_override helper directly ------------------------------


def test_coerce_override_list_2el_returns_tuple():
    assert emoji_config_service._coerce_override(["a", "b"]) == ("a", "b")


def test_coerce_override_dict_returns_tuple():
    assert emoji_config_service._coerce_override({"custom_id": "x", "fallback": "y"}) == ("x", "y")


def test_coerce_override_rejects_bad_inputs():
    assert emoji_config_service._coerce_override(None) is None
    assert emoji_config_service._coerce_override([]) is None
    assert emoji_config_service._coerce_override(["one_elem"]) is None
    assert emoji_config_service._coerce_override(["too", "many", "args"]) is None
    assert emoji_config_service._coerce_override({}) is None
    assert emoji_config_service._coerce_override({"custom_id": "x"}) is None
    assert emoji_config_service._coerce_override({"fallback": ""}) is None
    assert emoji_config_service._coerce_override("not an override") is None
    assert emoji_config_service._coerce_override(42) is None


# --- Whitelist + module surface ------------------------------------


def test_editable_fields_whitelist():
    assert (
        frozenset(
            {
                "category",
                "name_uz",
                "name_ru",
                "name_en",
                "static_emoji",
                "custom_emoji_id",
                "order_idx",
            }
        )
        == emoji_config_service.EDITABLE_FIELDS
    )


def test_invalidate_cache_resets_state():
    assert emoji_config_service._cache["configs"] is not None
    emoji_config_service.invalidate_cache()
    assert emoji_config_service._cache["configs"] is None
    assert emoji_config_service._cache["ts"] == 0.0


# --- Translator integration via i18n_service ----------------------


def test_translator_emoji_marker_substitution():
    """Strings containing `<e:code>` markers get substituted on every call."""
    from app.services.i18n_service import get_translator

    _ = get_translator("uz")
    # `_("emoji-...")` returns just the emoji — exercises the dedicated key path
    assert _("emoji-scene-night") == "🌙"
    assert _("emoji-status-death") == '<tg-emoji emoji-id="5269123456789012345">💀</tg-emoji>'


def test_translator_unknown_emoji_code_falls_back_to_defaults():
    """If the cache misses for a known DEFAULTS code, the static fallback
    is still returned so we never inject the raw marker into Telegram."""
    from app.db.models.emoji_config import DEFAULT_EMOJI_CONFIGS
    from app.services.i18n_service import _emoji_safe_fallback

    # Pick one we KNOW is in DEFAULTS but NOT in our test cache
    assert "scene-finished" not in emoji_config_service._cache["configs"]
    # Emoji service returns None …
    assert emoji_config_service.emoji_html_sync("scene-finished") is None
    # … but the safe-fallback path digs into DEFAULTS for the static emoji
    expected = next(
        s["static_emoji"] for s in DEFAULT_EMOJI_CONFIGS if s["code"] == "scene-finished"
    )
    assert _emoji_safe_fallback("scene-finished") == expected


def test_translator_emoji_overrides_apply():
    from app.services.i18n_service import get_translator

    _ = get_translator("uz", emoji_overrides={"scene-night": ["1234", "🌜"]})
    assert _("emoji-scene-night") == '<tg-emoji emoji-id="1234">🌜</tg-emoji>'
