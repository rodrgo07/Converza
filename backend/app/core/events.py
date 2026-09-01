import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.sse_subscribers: Dict[int, Set[asyncio.Queue]] = {}

    async def connect(self, websocket: WebSocket, company_id: int):
        await websocket.accept()
        if company_id not in self.active_connections:
            self.active_connections[company_id] = set()
        self.active_connections[company_id].add(websocket)

    def disconnect(self, websocket: WebSocket, company_id: int):
        if company_id in self.active_connections:
            self.active_connections[company_id].discard(websocket)
            if not self.active_connections[company_id]:
                del self.active_connections[company_id]

    async def broadcast_to_company(self, company_id: int, event_type: str, data: Any):
        payload = {'type': event_type, 'data': data}
        json_data = json.dumps(payload, default=str)
        if company_id in self.active_connections:
            dead = set()
            for ws in list(self.active_connections[company_id]):
                try:
                    await ws.send_text(json_data)
                except Exception:
                    dead.add(ws)
            for d in dead:
                self.active_connections[company_id].discard(d)

        if company_id in self.sse_subscribers:
            for q in list(self.sse_subscribers[company_id]):
                try:
                    q.put_nowait(payload)
                except Exception:
                    pass

    def subscribe_sse(self, company_id: int) -> asyncio.Queue:
        if company_id not in self.sse_subscribers:
            self.sse_subscribers[company_id] = set()
        q: asyncio.Queue = asyncio.Queue()
        self.sse_subscribers[company_id].add(q)
        return q

    def unsubscribe_sse(self, company_id: int, queue: asyncio.Queue):
        if company_id in self.sse_subscribers:
            self.sse_subscribers[company_id].discard(queue)
            if not self.sse_subscribers[company_id]:
                del self.sse_subscribers[company_id]

manager = ConnectionManager()
