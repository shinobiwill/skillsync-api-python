from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: user_id={user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected: user_id={user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")
                    disconnected.add(connection)

            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast(self, message: dict):
        for user_id, connections in self.active_connections.items():
            await self.send_personal_message(message, user_id)


manager = ConnectionManager()
