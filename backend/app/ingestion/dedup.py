from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.schemas import RawArticle

logger = logging.getLogger(__name__)


async def filter_duplicates(
    session: AsyncSession,
    raw_articles: list[RawArticle],
) -> list[RawArticle]:
    """Remove articles whose URL already exists in the database."""
    if not raw_articles:
        return []

    urls = [str(a.url) for a in raw_articles]

    result = await session.execute(
        select(Article.url).where(Article.url.in_(urls))
    )
    existing_urls: set[str] = {row[0] for row in result.all()}

    new_articles = [a for a in raw_articles if str(a.url) not in existing_urls]

    dupes = len(raw_articles) - len(new_articles)
    if dupes:
        logger.info("dedup: %d duplicates filtered, %d new", dupes, len(new_articles))

    return new_articles
