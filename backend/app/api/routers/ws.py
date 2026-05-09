"""WebSocket — real-time updates for admin panel.

Bosqich 3 da to'liq qo'llanadi.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


@router.websocket("/admin")
async def admin_ws(websocket: WebSocket) -> None:
    """Admin paneli uchun real-time WebSocket — placeholder."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WS received: {data}")
            await websocket.send_json({"echo": data})
    except WebSocketDisconnect:
        logger.info("WS client disconnected")
