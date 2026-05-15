"""WebSocket — real-time admin & SA panel updates.

Endpoints:
  /ws/admin                 — JWT (?token=). Global feed (all groups).
  /ws/admin/group/{gid}     — JWT (?token=). Single group's live events.
  /ws/sa/group/{gid}        — Telegram SA (?init_data=). Single group.

Per-group sockets receive only events tagged with that group_id, plus
nothing from other groups — keeps the live spectator page focused.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from app.api.auth.jwt_helpers import decode_token
from app.config import settings
from app.db.models import AdminAccount
from app.services.ws_broker import AdminBroker
from app.utils.webapp_auth import validate_init_data

router = APIRouter()


async def _validate_jwt(token: str) -> bool:
    payload = decode_token(token)
    if payload is None:
        return False
    admin_id = payload.get("sub")
    if admin_id is None:
        return False
    admin = await AdminAccount.get_or_none(id=admin_id)
    return admin is not None and admin.is_active


async def _validate_sa_init_data(init_data: str) -> bool:
    # Debug bypass — accept secret_key like the HTTP SA dep does.
    if settings.debug and init_data == settings.secret_key.get_secret_value():
        return bool(settings.super_admin_ids)
    parsed = validate_init_data(init_data)
    if parsed is None:
        return False
    user_obj = parsed.get("user")
    if not isinstance(user_obj, dict) or "id" not in user_obj:
        return False
    try:
        tg_id = int(user_obj["id"])
    except (TypeError, ValueError):
        return False
    return tg_id in settings.super_admin_ids


@router.websocket("/admin")
async def admin_ws_global(websocket: WebSocket, token: str = Query(...)) -> None:
    """Admin panel global feed — every event from every group."""
    if not await _validate_jwt(token):
        await websocket.close(code=4401, reason="Invalid token")
        return
    await websocket.accept()
    await AdminBroker.subscribe(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive ping
    except WebSocketDisconnect:
        logger.debug("Admin WS (global) disconnected")
    except Exception as e:
        logger.warning(f"Admin WS (global) error: {e}")
    finally:
        await AdminBroker.unsubscribe(websocket)


@router.websocket("/admin/group/{group_id}")
async def admin_ws_group(websocket: WebSocket, group_id: int, token: str = Query(...)) -> None:
    """Per-group feed for JWT admin panel."""
    if not await _validate_jwt(token):
        await websocket.close(code=4401, reason="Invalid token")
        return
    await websocket.accept()
    await AdminBroker.subscribe(websocket, group_id=group_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.debug(f"Admin WS group:{group_id} disconnected")
    except Exception as e:
        logger.warning(f"Admin WS group:{group_id} error: {e}")
    finally:
        await AdminBroker.unsubscribe(websocket, group_id=group_id)


@router.websocket("/sa/group/{group_id}")
async def sa_ws_group(websocket: WebSocket, group_id: int, init_data: str = Query(...)) -> None:
    """Per-group feed for Telegram WebApp SA panel."""
    if not await _validate_sa_init_data(init_data):
        await websocket.close(code=4401, reason="Invalid init data")
        return
    await websocket.accept()
    await AdminBroker.subscribe(websocket, group_id=group_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.debug(f"SA WS group:{group_id} disconnected")
    except Exception as e:
        logger.warning(f"SA WS group:{group_id} error: {e}")
    finally:
        await AdminBroker.unsubscribe(websocket, group_id=group_id)
