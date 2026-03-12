from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.ingestion.dedup import filter_duplicates
from app.ingestion.sources.arxiv import ArxivSource
from app.ingestion.sources.base import BaseSource
from app.ingestion.sources.blogs import BlogsSource
from app.ingestion.sources.devto import DevToSource
from app.ingestion.sources.github_trending import GitHubTrendingSource
from app.ingestion.sources.hackernews import HackerNewsSource
from app.ingestion.sources.huggingface import HuggingFaceSource
from app.ingestion.sources.paperswithcode import PapersWithCodeSource
from app.ingestion.sources.reddit import RedditSource
from app.ingestion.sources.semanticscholar import SemanticScholarSource
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
    RedditSource,
    PapersWithCodeSource,
    DevToSource,
    GitHubTrendingSource,
    SemanticScholarSource,
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
        analysis, used_fallback = await analyze_article(
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
            needs_reanalysis=used_fallback,
            embedding=embedding,
            published_at=raw.published_at,
        )

        async with session.begin_nested():
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

            if stats["stored"] > 0:
                await session.commit()
            else:
                await session.rollback()

        except Exception:
            try:
                await session.rollback()
            except Exception:
                pass
            logger.exception("Pipeline commit failed")

    logger.info(
        "Pipeline done — fetched: %d | new: %d | stored: %d | errors: %d",
        stats["fetched"],
        stats["new"],
        stats["stored"],
        stats["errors"],
    )

    return stats


async def retry_failed_analyses(batch_size: int = 20) -> dict:
    """Re-analyze articles that previously fell back to keyword extraction."""
    stats = {"found": 0, "updated": 0, "still_failed": 0}

    async with async_session_factory() as session:
        result = await session.execute(
            select(Article)
            .where(Article.needs_reanalysis.is_(True))
            .order_by(Article.created_at.desc())
            .limit(batch_size)
        )
        articles = list(result.scalars().all())
        stats["found"] = len(articles)

        if not articles:
            return stats

        for article in articles:
            try:
                analysis, used_fallback = await analyze_article(
                    title=article.title,
                    content=article.content,
                    source=article.source,
                )

                if used_fallback:
                    stats["still_failed"] += 1
                    continue

                article.category_tags = analysis.category_tags
                article.model_tags = analysis.model_tags
                article.summary_en = analysis.summary_en
                article.summary_tr = analysis.summary_tr
                article.importance = analysis.importance
                article.key_metric = analysis.key_metric or None
                article.is_llm_related = analysis.is_llm_related
                article.needs_reanalysis = False

                embed_text = f"{article.title} {analysis.summary_en or article.content[:500]}"
                article.embedding = await generate_embedding(embed_text)

                stats["updated"] += 1
            except Exception:
                stats["still_failed"] += 1
                logger.exception("Retry failed for: %s", article.title[:60])

        if stats["updated"] > 0:
            await session.commit()

    logger.info(
        "Retry done — found: %d | updated: %d | still_failed: %d",
        stats["found"],
        stats["updated"],
        stats["still_failed"],
    )
    return stats
