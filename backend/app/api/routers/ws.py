"""WebSocket — real-time admin panel updates."""

from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from app.api.auth.jwt_helpers import decode_token
from app.services.ws_broker import AdminBroker

router = APIRouter()


@router.websocket("/admin")
async def admin_ws(websocket: WebSocket, token: str = Query(...)) -> None:
    """Admin paneli uchun real-time WebSocket. JWT auth via ?token= query."""
    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=4401, reason="Invalid token")
        return

    await websocket.accept()
    await AdminBroker.subscribe(websocket)

    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        logger.debug("Admin WS disconnected")
    except Exception as e:
        logger.warning(f"Admin WS error: {e}")
    finally:
        await AdminBroker.unsubscribe(websocket)
