from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.ingestion.pipeline import retry_failed_analyses, run_pipeline
from app.ingestion.sources.arxiv import ArxivSource
from app.ingestion.sources.blogs import BlogsSource
from app.ingestion.sources.devto import DevToSource
from app.ingestion.sources.github_trending import GitHubTrendingSource
from app.ingestion.sources.hackernews import HackerNewsSource
from app.ingestion.sources.huggingface import HuggingFaceSource
from app.ingestion.sources.paperswithcode import PapersWithCodeSource
from app.ingestion.sources.reddit import RedditSource
from app.ingestion.sources.semanticscholar import SemanticScholarSource

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_job(source_name: str, source_cls: type) -> None:
    logger.info("Scheduler: starting %s job", source_name)
    try:
        stats = await run_pipeline(source_cls)
        logger.info(
            "Scheduler: %s completed — fetched=%d new=%d stored=%d errors=%d",
            source_name,
            stats["fetched"],
            stats["new"],
            stats["stored"],
            stats["errors"],
        )
    except Exception:
        logger.exception("Scheduler: %s job failed", source_name)


def setup_scheduler() -> AsyncIOScheduler:
    settings = get_settings()

    jobs = [
        ("arxiv", ArxivSource, settings.ARXIV_INTERVAL),
        ("hackernews", HackerNewsSource, settings.HACKERNEWS_INTERVAL),
        ("huggingface", HuggingFaceSource, settings.HUGGINGFACE_INTERVAL),
        ("blogs", BlogsSource, settings.BLOGS_INTERVAL),
        ("reddit", RedditSource, 20),
        ("paperswithcode", PapersWithCodeSource, 60),
        ("devto", DevToSource, 30),
        ("github_trending", GitHubTrendingSource, 60),
        ("semanticscholar", SemanticScholarSource, 60),
    ]

    for name, cls, interval_minutes in jobs:
        scheduler.add_job(
            _run_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[name, cls],
            id=f"ingest_{name}",
            name=f"Ingest {name}",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,
        )
        logger.info(
            "Scheduler: registered %s (every %d min)", name, interval_minutes
        )

    scheduler.add_job(
        _run_retry,
        trigger=IntervalTrigger(minutes=10),
        id="retry_analyses",
        name="Retry failed analyses",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )
    logger.info("Scheduler: registered retry_analyses (every 10 min)")

    return scheduler


async def _run_retry() -> None:
    logger.info("Scheduler: starting retry job")
    try:
        stats = await retry_failed_analyses(batch_size=20)
        logger.info(
            "Scheduler: retry completed — found=%d updated=%d still_failed=%d",
            stats["found"],
            stats["updated"],
            stats["still_failed"],
        )
    except Exception:
        logger.exception("Scheduler: retry job failed")


async def run_initial_fetch() -> None:
    """Run all sources once at startup to populate the feed."""
    logger.info("Scheduler: running initial fetch for all sources")
    try:
        stats = await run_pipeline()
        logger.info(
            "Scheduler: initial fetch done — fetched=%d new=%d stored=%d errors=%d",
            stats["fetched"],
            stats["new"],
            stats["stored"],
            stats["errors"],
        )
    except Exception:
        logger.exception("Scheduler: initial fetch failed")
