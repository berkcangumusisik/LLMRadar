from __future__ import annotations

import asyncio
import logging

from app.core.supabase import get_supabase_client
from app.models.schemas import ArticleOut
from app.realtime.manager import manager

logger = logging.getLogger(__name__)

_listener_task: asyncio.Task | None = None


def _row_to_article_out(row: dict) -> ArticleOut | None:
    try:
        row.pop("embedding", None)
        return ArticleOut(**row)
    except Exception:
        logger.warning("Failed to parse realtime row: %s", row.get("id"))
        return None


async def _listen_inserts() -> None:
    client = get_supabase_client()

    channel = client.channel("articles-inserts")

    def _on_insert(payload: dict) -> None:
        record = payload.get("record") or payload.get("new", {})
        if not record:
            return

        article = _row_to_article_out(record)
        if article is None:
            return

        loop = asyncio.get_event_loop()
        loop.create_task(manager.broadcast_new_article(article))
        logger.debug("Broadcasted new article: %s", article.title[:60])

    channel.on_postgres_changes(
        event="INSERT",
        schema="public",
        table="articles",
        callback=_on_insert,
    ).subscribe()

    logger.info("Supabase Realtime listener subscribed to articles INSERT")

    while True:
        await asyncio.sleep(60)


async def start_broadcaster() -> None:
    global _listener_task
    if _listener_task is None or _listener_task.done():
        _listener_task = asyncio.create_task(_listen_inserts())
        logger.info("Broadcaster started")


async def stop_broadcaster() -> None:
    global _listener_task
    if _listener_task and not _listener_task.done():
        _listener_task.cancel()
        try:
            await _listener_task
        except asyncio.CancelledError:
            pass
        logger.info("Broadcaster stopped")
