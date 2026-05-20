"""i18n service — Project Fluent (`fluent.runtime`)."""

import re
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

from fluent.runtime import FluentLocalization, FluentResourceLoader
from loguru import logger

# `<e:code>` markers in .ftl strings get substituted at translation time
# with the matching EmojiConfig entry (Unicode or `<tg-emoji>` HTML).
# Group capture is restricted to slug-safe chars so we never accidentally
# eat surrounding markup.
_EMOJI_TAG_RE = re.compile(r"<e:([a-z0-9_-]+)>")


@lru_cache(maxsize=128)
def _emoji_safe_fallback(code: str) -> str:
    """Static fallback used only when the EmojiConfig cache is cold during
    boot — pulled from the module-level DEFAULTS so we never inject the
    raw marker into a Telegram message (which would 400 on parse)."""
    from app.db.models.emoji_config import DEFAULT_EMOJI_CONFIGS

    for spec in DEFAULT_EMOJI_CONFIGS:
        if spec["code"] == code:
            return spec["static_emoji"]
    return "❓"


LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"
DEFAULT_LOCALE = "uz"
SUPPORTED_LOCALES = ("uz", "ru", "en")


# Translator type — call signature: _("key", **vars) -> str
Translator = Callable[..., str]


@lru_cache(maxsize=8)
def _build_localization(locale: str) -> FluentLocalization:
    """Build FluentLocalization for a given locale (cached)."""
    if locale not in SUPPORTED_LOCALES:
        logger.warning(f"Unsupported locale '{locale}', falling back to {DEFAULT_LOCALE}")
        locale = DEFAULT_LOCALE

    loader = FluentResourceLoader(str(LOCALES_DIR / "{locale}"))
    return FluentLocalization(
        locales=[locale, DEFAULT_LOCALE],
        resource_ids=["main.ftl"],
        resource_loader=loader,
    )


def get_translator(
    locale: str,
    role_overrides: dict | None = None,
    emoji_overrides: dict | None = None,
) -> Translator:
    """Return a translator function for the given locale.

    Usage:
        _ = get_translator('uz')
        _("start-welcome", username="Ali")  # → "Salom, Ali!"

    Three namespaces are intercepted so super-admin / per-group edits
    propagate to every bot message without redeploys:

    * `role-{slug}` → `role_config_service.role_label_sync()` —
      returns "{emoji} {localised name}".
    * `emoji-{code}` → `emoji_config_service.emoji_html_sync()` —
      returns just the emoji (Unicode or `<tg-emoji>` HTML).
    * Any `.ftl` string containing `<e:CODE>` markers gets those
      markers substituted with the rendered emoji at format time, so
      handlers stay oblivious — only `.ftl` strings change to opt in.

    Both `role_overrides` and `emoji_overrides` come from
    `GroupSettings.display.{role_emojis, custom_emojis}` via the
    middleware. Fall-through behaviour: cold cache → static defaults so
    handlers never get the raw marker.
    """
    l10n = _build_localization(locale)
    # Lazy imports — avoid bootstrap circular when i18n loads very early.
    from app.services import emoji_config_service, role_config_service

    def _substitute_emoji_tags(text: str) -> str:
        if "<e:" not in text:
            return text

        def repl(m: re.Match[str]) -> str:
            code = m.group(1)
            v = emoji_config_service.emoji_html_sync(code, overrides=emoji_overrides)
            return v if v is not None else _emoji_safe_fallback(code)

        return _EMOJI_TAG_RE.sub(repl, text)

    def _(key: str, **kwargs: Any) -> str:
        # Dynamic role labels
        if key.startswith("role-") and not key.startswith("role-desc-"):
            slug = key[len("role-") :]
            dyn = role_config_service.role_label_sync(slug, locale, overrides=role_overrides)
            if dyn is not None:
                return _substitute_emoji_tags(dyn)

        # Dynamic standalone emoji (no name attached)
        elif key.startswith("emoji-"):
            code = key[len("emoji-") :]
            dyn = emoji_config_service.emoji_html_sync(code, overrides=emoji_overrides)
            if dyn is not None:
                return dyn
            return _emoji_safe_fallback(code)

        result = l10n.format_value(key, kwargs if kwargs else None)
        if result == key:
            logger.warning(f"Missing i18n key: '{key}' for locale '{locale}'")
        return _substitute_emoji_tags(result)

    return _
