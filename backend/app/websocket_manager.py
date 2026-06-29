from fastapi import WebSocket
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_location(self, user_id: int, lat: float, lng: float):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json({"lat": lat, "lng": lng})

manager = ConnectionManager()
