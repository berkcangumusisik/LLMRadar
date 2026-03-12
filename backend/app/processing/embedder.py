from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _load_model() -> SentenceTransformer:
    settings = get_settings()
    logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
    return SentenceTransformer(settings.EMBEDDING_MODEL)


async def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dim embedding for the given text using all-MiniLM-L6-v2."""
    model = _load_model()
    vector = await asyncio.to_thread(
        model.encode, text, normalize_embeddings=True
    )
    return np.asarray(vector, dtype=np.float32).tolist()


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    if not texts:
        return []
    model = _load_model()
    vectors = await asyncio.to_thread(
        model.encode, texts, normalize_embeddings=True, batch_size=32
    )
    return [np.asarray(v, dtype=np.float32).tolist() for v in vectors]
