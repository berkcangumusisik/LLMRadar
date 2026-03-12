from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.article import Article
from app.models.schemas import ArticleOut, FeedResponse, RelatedArticle
from app.rag.related import find_related_articles

router = APIRouter(prefix="/api", tags=["articles"])


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str | None = Query(None),
    category: str | None = Query(None),
    model_tag: str | None = Query(None),
    min_importance: int | None = Query(None, ge=1, le=10),
    session: AsyncSession = Depends(get_session),
) -> FeedResponse:
    query = select(Article).where(Article.is_llm_related.is_(True))
    count_query = select(func.count(Article.id)).where(Article.is_llm_related.is_(True))

    if source:
        query = query.where(Article.source == source)
        count_query = count_query.where(Article.source == source)

    if category:
        query = query.where(Article.category_tags.any(category))
        count_query = count_query.where(Article.category_tags.any(category))

    if model_tag:
        query = query.where(Article.model_tags.any(model_tag))
        count_query = count_query.where(Article.model_tags.any(model_tag))

    if min_importance is not None:
        query = query.where(Article.importance >= min_importance)
        count_query = count_query.where(Article.importance >= min_importance)

    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Article.published_at.desc()).offset(offset).limit(page_size)

    result = await session.execute(query)
    articles = result.scalars().all()

    items = [ArticleOut.model_validate(a) for a in articles]

    return FeedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.get("/articles/{article_id}", response_model=ArticleOut)
async def get_article(
    article_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ArticleOut:
    result = await session.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one()
    return ArticleOut.model_validate(article)


@router.get("/articles/{article_id}/related", response_model=list[RelatedArticle])
async def get_related(
    article_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[RelatedArticle]:
    result = await session.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one()

    text = f"{article.title} {article.summary_en or article.content[:500]}"
    return await find_related_articles(article_id, text)


@router.get("/sources", response_model=list[dict])
async def get_sources(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    result = await session.execute(
        select(Article.source, func.count(Article.id).label("count"))
        .group_by(Article.source)
        .order_by(func.count(Article.id).desc())
    )
    return [{"source": row[0], "count": row[1]} for row in result.all()]


@router.get("/stats")
async def get_stats(
    session: AsyncSession = Depends(get_session),
) -> dict:
    total = await session.execute(select(func.count(Article.id)))
    llm_related = await session.execute(
        select(func.count(Article.id)).where(Article.is_llm_related.is_(True))
    )
    avg_importance = await session.execute(
        select(func.avg(Article.importance)).where(Article.is_llm_related.is_(True))
    )

    return {
        "total_articles": total.scalar() or 0,
        "llm_related": llm_related.scalar() or 0,
        "avg_importance": round(float(avg_importance.scalar() or 0), 1),
    }
