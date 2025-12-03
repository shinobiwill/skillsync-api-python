from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket_service import manager
from app.core.dependencies import get_current_user
import logging

router = APIRouter(prefix="/api/ws", tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = None):
    user_id = None
    try:
        if token:
            try:
                user = await get_current_user(token)
                user_id = str(user.get("sub", user.get("id")))
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                await websocket.close(code=4001, reason="Invalid token")
                return
        else:
            await websocket.close(code=4001, reason="Missing token")
            return

        await manager.connect(websocket, user_id)

        while True:
            data = await websocket.receive_text()

    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user_id:
            manager.disconnect(websocket, user_id)
