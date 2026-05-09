"""Audit log service — logs super admin actions."""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.db.models import AdminAccount, AuditLog, User


async def log_action(
    action: str,
    actor: User | AdminAccount | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Persist an audit entry.

    Args:
        action: e.g. 'user.ban', 'group.block', 'diamonds.grant', 'premium.grant'
        actor: User (Telegram-linked) or AdminAccount (login-based)
        target_type: 'user' | 'group' | 'game'
        target_id: ID as string
        payload: arbitrary context (amounts, reasons)
    """
    actor_user = actor if isinstance(actor, User) else None
    actor_admin = actor if isinstance(actor, AdminAccount) else None

    entry = await AuditLog.create(
        actor=actor_user,
        actor_admin=actor_admin,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    actor_label = (
        f"user:{actor_user.id}"
        if actor_user
        else (f"admin:{actor_admin.username}" if actor_admin else "system")
    )
    logger.info(f"AUDIT [{actor_label}] {action} → {target_type}:{target_id}")
    return entry
