from __future__ import annotations

import logging
import uuid

from app.core.config import get_settings
from app.core.supabase import get_supabase_client
from app.models.schemas import RelatedArticle
from app.processing.embedder import generate_embedding

logger = logging.getLogger(__name__)


async def find_related_articles(
    article_id: uuid.UUID,
    text: str,
) -> list[RelatedArticle]:
    """Find similar articles using pgvector cosine similarity via Supabase RPC."""
    settings = get_settings()

    embedding = await generate_embedding(text)

    client = get_supabase_client()
    try:
        response = client.rpc(
            "match_articles",
            {
                "query_embedding": embedding,
                "match_threshold": settings.SIMILARITY_THRESHOLD,
                "match_count": settings.RELATED_MATCH_COUNT,
                "exclude_id": str(article_id),
            },
        ).execute()
    except Exception:
        logger.exception("RPC match_articles failed for %s", article_id)
        return []

    results: list[RelatedArticle] = []
    for row in response.data or []:
        try:
            results.append(RelatedArticle(**row))
        except Exception:
            logger.warning("Skipping malformed related article row: %s", row)

    logger.info(
        "Related articles for %s: found %d (threshold=%.2f)",
        article_id,
        len(results),
        settings.SIMILARITY_THRESHOLD,
    )

    return results
