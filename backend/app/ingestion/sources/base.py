from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.models.schemas import RawArticle

logger = logging.getLogger(__name__)


class BaseSource(abc.ABC):

    name: str = "unknown"
    timeout: float = 30.0

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            headers={"User-Agent": "LLMRadar/1.0"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    @abc.abstractmethod
    async def fetch(self) -> list[RawArticle]:
        ...

    async def safe_fetch(self) -> list[RawArticle]:
        try:
            articles = await self.fetch()
            logger.info("%s: fetched %d articles", self.name, len(articles))
            return articles
        except Exception:
            logger.exception("%s: fetch failed", self.name)
            return []
