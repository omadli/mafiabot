"""i18n service — Project Fluent (`fluent.runtime`)."""

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

from fluent.runtime import FluentLocalization, FluentResourceLoader
from loguru import logger

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


def get_translator(locale: str) -> Translator:
    """Return a translator function for the given locale.

    Usage:
        _ = get_translator('uz')
        _("start-welcome", username="Ali")  # → "Salom, Ali!"
    """
    l10n = _build_localization(locale)

    def _(key: str, **kwargs: Any) -> str:
        result = l10n.format_value(key, kwargs if kwargs else None)
        # FluentLocalization returns the key itself if missing — log it
        if result == key:
            logger.warning(f"Missing i18n key: '{key}' for locale '{locale}'")
        return result

    return _
