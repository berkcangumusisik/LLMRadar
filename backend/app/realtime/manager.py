from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket

from app.core.config import get_settings
from app.models.schemas import ArticleOut, WSMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info("WS connected — total: %d", self.active_count)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)
        logger.info("WS disconnected — total: %d", self.active_count)

    async def broadcast(self, message: WSMessage) -> None:
        payload = message.model_dump_json()

        async with self._lock:
            targets = list(self._connections)

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)
            logger.info("Removed %d dead connections", len(dead))

    async def send_personal(self, ws: WebSocket, message: WSMessage) -> None:
        try:
            await ws.send_text(message.model_dump_json())
        except Exception:
            logger.warning("Failed to send personal message")

    async def broadcast_new_article(self, article: ArticleOut) -> None:
        msg = WSMessage(type="new_article", data=article)
        await self.broadcast(msg)

    async def ping_all(self) -> None:
        msg = WSMessage(type="ping", data=None)
        await self.broadcast(msg)

    async def start_ping_loop(self) -> None:
        settings = get_settings()
        while True:
            await asyncio.sleep(settings.WS_PING_INTERVAL)
            await self.ping_all()


manager = ConnectionManager()
