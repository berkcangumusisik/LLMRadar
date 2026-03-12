from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.article import Article
from app.models.schemas import ArticleOut, WSMessage
from app.realtime.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = payload.get("type")

            if msg_type == "search":
                query_text = payload.get("query", "").strip()
                if query_text:
                    results = await _search_articles(query_text)
                    response = WSMessage(type="search_results", data=results)
                    await manager.send_personal(ws, response)

            elif msg_type == "pong":
                pass

    except WebSocketDisconnect:
        await manager.disconnect(ws)
    except Exception:
        logger.exception("WebSocket error")
        await manager.disconnect(ws)


async def _search_articles(query: str) -> list[ArticleOut]:
    pattern = f"%{query}%"
    async with async_session_factory() as session:
        result = await session.execute(
            select(Article)
            .where(
                Article.is_llm_related.is_(True),
                Article.title.ilike(pattern) | Article.summary_en.ilike(pattern) | Article.summary_tr.ilike(pattern),
            )
            .order_by(Article.importance.desc(), Article.published_at.desc())
            .limit(20)
        )
        articles = result.scalars().all()
        return [ArticleOut.model_validate(a) for a in articles]
