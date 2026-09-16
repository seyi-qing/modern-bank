"""
In-memory WebSocket connection manager for live notifications.
"""

from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if user_id not in self.active:
                self.active[user_id] = set()
            self.active[user_id].add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket):
        async with self._lock:
            if user_id in self.active:
                self.active[user_id].discard(websocket)
                if not self.active[user_id]:
                    del self.active[user_id]

    async def send_personal(self, user_id: int, message: dict):
        if user_id not in self.active:
            return
        dead = []
        for ws in list(self.active.get(user_id, set())):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)

    async def broadcast(self, message: dict):
        for uid in list(self.active.keys()):
            await self.send_personal(uid, message)


manager = ConnectionManager()
