"""Telegram WebApp initData validation.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
from datetime import UTC, datetime
from urllib.parse import parse_qsl

from app.config import settings


# Cache the secret key (HMAC-SHA256 of bot token with key="WebAppData")
def _secret_key() -> bytes:
    return hmac.new(
        b"WebAppData",
        settings.bot_token.get_secret_value().encode("utf-8"),
        hashlib.sha256,
    ).digest()


def validate_init_data(init_data: str, max_age_seconds: int = 86400) -> dict | None:
    """Verify and parse Telegram WebApp initData.

    Returns parsed dict (with `user`, `auth_date`, etc.) if valid, None otherwise.
    """
    if not init_data:
        return None

    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if received_hash is None:
        return None

    # Check auth_date
    try:
        auth_date = int(parsed.get("auth_date", "0"))
    except ValueError:
        return None
    if auth_date <= 0:
        return None
    age = datetime.now(UTC).timestamp() - auth_date
    if age > max_age_seconds:
        return None

    # Build data-check-string
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    expected_hash = hmac.new(
        _secret_key(),
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    # Decode user JSON if present
    if "user" in parsed:
        with contextlib.suppress(json.JSONDecodeError):
            parsed["user"] = json.loads(parsed["user"])

    return parsed
