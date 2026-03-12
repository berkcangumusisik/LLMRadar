from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.ingestion.dedup import filter_duplicates
from app.ingestion.sources.arxiv import ArxivSource
from app.ingestion.sources.base import BaseSource
from app.ingestion.sources.blogs import BlogsSource
from app.ingestion.sources.hackernews import HackerNewsSource
from app.ingestion.sources.huggingface import HuggingFaceSource
from app.ingestion.sources.rsshub import RSSHubSource
from app.models.article import Article
from app.models.schemas import RawArticle
from app.processing.embedder import generate_embedding
from app.processing.gemini import analyze_article

logger = logging.getLogger(__name__)

ALL_SOURCES: list[type[BaseSource]] = [
    ArxivSource,
    HackerNewsSource,
    HuggingFaceSource,
    BlogsSource,
    RSSHubSource,
]


async def run_source(source_cls: type[BaseSource]) -> list[RawArticle]:
    source = source_cls()
    try:
        return await source.safe_fetch()
    finally:
        await source.close()


async def process_and_store(
    session: AsyncSession,
    raw: RawArticle,
) -> Article | None:
    try:
        analysis = await analyze_article(
            title=raw.title,
            content=raw.content,
            source=raw.source,
        )

        embed_text = f"{raw.title} {analysis.summary_en or raw.content[:500]}"
        embedding = await generate_embedding(embed_text)

        article = Article(
            title=raw.title,
            content=raw.content,
            url=str(raw.url),
            source=raw.source,
            author=raw.author,
            category_tags=analysis.category_tags,
            model_tags=analysis.model_tags,
            summary_en=analysis.summary_en,
            summary_tr=analysis.summary_tr,
            importance=analysis.importance,
            key_metric=analysis.key_metric or None,
            is_llm_related=analysis.is_llm_related,
            embedding=embedding,
            published_at=raw.published_at,
        )

        session.add(article)
        await session.flush()
        return article

    except Exception:
        logger.exception("Failed to process: %s", raw.title[:80])
        return None


async def run_pipeline(source_cls: type[BaseSource] | None = None) -> dict:
    """Run the full ingestion pipeline for one or all sources.

    Returns stats: {fetched, new, stored, errors}
    """
    stats = {"fetched": 0, "new": 0, "stored": 0, "errors": 0}

    if source_cls:
        sources_to_run = [source_cls]
    else:
        sources_to_run = ALL_SOURCES

    all_raw: list[RawArticle] = []
    for src_cls in sources_to_run:
        articles = await run_source(src_cls)
        all_raw.extend(articles)

    stats["fetched"] = len(all_raw)

    if not all_raw:
        logger.info("Pipeline: no articles fetched")
        return stats

    async with async_session_factory() as session:
        try:
            new_articles = await filter_duplicates(session, all_raw)
            stats["new"] = len(new_articles)

            for raw in new_articles:
                article = await process_and_store(session, raw)
                if article:
                    stats["stored"] += 1
                else:
                    stats["errors"] += 1

            await session.commit()

        except Exception:
            await session.rollback()
            logger.exception("Pipeline commit failed")
            raise

    logger.info(
        "Pipeline done — fetched: %d | new: %d | stored: %d | errors: %d",
        stats["fetched"],
        stats["new"],
        stats["stored"],
        stats["errors"],
    )

    return stats
