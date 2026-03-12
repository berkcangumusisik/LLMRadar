from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.ingestion.pipeline import run_pipeline
from app.ingestion.sources.arxiv import ArxivSource
from app.ingestion.sources.blogs import BlogsSource
from app.ingestion.sources.hackernews import HackerNewsSource
from app.ingestion.sources.huggingface import HuggingFaceSource
from app.ingestion.sources.rsshub import RSSHubSource

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
        ("rsshub", RSSHubSource, settings.RSSHUB_INTERVAL),
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

    return scheduler


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
