"""Curated list of overridable message templates.

Group admins can override these via the WebApp; the bot reads
`GroupSettings.messages.<key>` and falls back to the i18n default if no
override is set. To open a new key for override:

1. Add it here with a stable `key`, the i18n key it falls back to, and
   per-locale `notes` describing available `{placeholders}`.
2. In the handler, replace `_("foo")` with `render_template(state, "foo", ...)`.

Keeping the list curated (instead of "every i18n string") is intentional —
it avoids exposing engine-internal strings whose placeholders the user
could break by accident.
"""

from __future__ import annotations

from app.services.i18n_service import get_translator

# Each entry: stable `key` used in GroupSettings.messages, the i18n key
# used as fallback, and a short description shown in the editor.
#
# `leave_message` is the only message currently wired for override —
# `game.py:170` reads it from GroupSettings.messages and substitutes
# `{mention}` if present. New override slots should be added here AND
# wired in the handler before they show up in the editor.
OVERRIDABLE_MESSAGES: list[dict[str, str]] = [
    {
        "key": "leave_message",
        "i18n_key": "leave-broadcast",
        "placeholders": "{mention}",
    },
]


def list_templates(locale: str, current_overrides: dict) -> list[dict]:
    """Return the editor model: per key, default from i18n + current override."""
    t = get_translator(locale)
    out: list[dict] = []
    for spec in OVERRIDABLE_MESSAGES:
        key = spec["key"]
        default = t(spec["i18n_key"])
        out.append(
            {
                "key": key,
                "default": default if default != spec["i18n_key"] else "",
                "override": current_overrides.get(key, ""),
                "placeholders": spec["placeholders"],
            }
        )
    return out


def render_template(
    overrides: dict, key: str, fallback_i18n_key: str, locale: str, **fmt_vars: object
) -> str:
    """Render a template — override if set, else i18n default. Format-safe.

    Bad `{placeholder}` in an admin's override should never crash the bot —
    fall back to the i18n default and log instead.
    """
    template = overrides.get(key) or get_translator(locale)(fallback_i18n_key)
    try:
        return template.format(**fmt_vars)
    except (KeyError, IndexError, ValueError):
        from loguru import logger

        logger.warning(
            f"Override template '{key}' has bad placeholder; falling back to default i18n"
        )
        return get_translator(locale)(fallback_i18n_key).format(**fmt_vars)
