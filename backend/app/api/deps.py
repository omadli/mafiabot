"""FastAPI dependencies — auth guards."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.api.auth.jwt_helpers import decode_token
from app.db.models import AdminAccount


async def get_current_admin(
    authorization: str | None = Header(default=None),
) -> AdminAccount:
    """Bearer JWT → AdminAccount."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    admin_id = payload.get("sub")
    if admin_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject")

    admin = await AdminAccount.get_or_none(id=admin_id)
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found or inactive"
        )
    return admin


def require_role(*allowed_roles: str):
    """Dependency factory — restrict endpoint to specific admin roles."""

    async def _check(admin: AdminAccount = Depends(get_current_admin)) -> AdminAccount:
        if admin.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return admin

    return _check
