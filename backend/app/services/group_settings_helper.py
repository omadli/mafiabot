"""Workaround for Tortoise 0.21 OneToOneField(pk=True) save() bug.

GroupSettings has its primary key declared as a OneToOneField:
    group = fields.OneToOneField("models.Group", related_name="settings",
                                  pk=True, on_delete=fields.CASCADE)

When calling `instance.save(update_fields=[...])` Tortoise 0.21 generates
SQL like:
    UPDATE "group_settings" SET "language" = $1 WHERE "group" = $2

…using the field NAME ("group") instead of the column NAME ("group_id").
PostgreSQL rejects this because `group` is a reserved word AND the column
literally doesn't exist (it's `group_id`). SQLite accepts it because it's
more forgiving.

Workaround: use a filter().update() query which lets us specify the column
explicitly. We pass values via kwargs so Tortoise builds an UPDATE with the
right column names.
"""

from __future__ import annotations

from typing import Any

from app.db.models import GroupSettings


async def save_settings_fields(s: GroupSettings, **fields: Any) -> None:
    """Update specific fields on a GroupSettings row, bypassing the save() bug.

    Usage:
        await save_settings_fields(s, language="ru", roles={...})

    Args:
        s: The GroupSettings instance whose `group_id` identifies the row.
        **fields: Field/value pairs to persist.
    """
    if not fields:
        return
    # Mirror in-memory so callers reading from `s` afterwards see the change
    for name, val in fields.items():
        setattr(s, name, val)
    await GroupSettings.filter(group_id=s.group_id).update(**fields)
