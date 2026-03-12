from __future__ import annotations

import datetime

from app.ingestion.sources.base import BaseSource, logger
from app.models.schemas import RawArticle

SS_API = "https://api.semanticscholar.org/graph/v1/paper/search"

QUERIES = [
    "large language model",
    "LLM reasoning",
    "AI agent",
]


class SemanticScholarSource(BaseSource):
    name = "semanticscholar"
    timeout = 30.0

    async def fetch(self) -> list[RawArticle]:
        articles: list[RawArticle] = []
        seen_urls: set[str] = set()
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        year = datetime.datetime.now(datetime.timezone.utc).year

        for query in QUERIES:
            try:
                items = await self._search(query, year, cutoff, seen_urls)
                articles.extend(items)
            except Exception as exc:
                logger.warning("semanticscholar/%s failed: %s", query[:20], exc)

        return articles

    async def _search(
        self,
        query: str,
        year: int,
        cutoff: datetime.datetime,
        seen_urls: set[str],
    ) -> list[RawArticle]:
        params = {
            "query": query,
            "limit": 20,
            "fields": "title,abstract,url,authors,publicationDate,year",
            "year": f"{year}-",
        }
        resp = await self._client.get(SS_API, params=params)
        resp.raise_for_status()
        data = resp.json()

        articles: list[RawArticle] = []
        for paper in data.get("data", []):
            title = (paper.get("title") or "").strip()
            abstract = (paper.get("abstract") or "").strip()
            url = paper.get("url", "")
            pub_date = paper.get("publicationDate", "")

            if not title or not url:
                continue

            if url in seen_urls:
                continue
            seen_urls.add(url)

            published_at = self._parse_date(pub_date)
            if published_at < cutoff:
                continue

            authors = paper.get("authors", [])
            author_names = [a.get("name", "") for a in authors[:3] if a.get("name")]
            author_str = ", ".join(author_names) if author_names else None

            articles.append(
                RawArticle(
                    title=title,
                    content=abstract or title,
                    url=url,
                    source="semanticscholar",
                    author=author_str,
                    published_at=published_at,
                )
            )

        return articles

    @staticmethod
    def _parse_date(raw: str) -> datetime.datetime:
        if not raw:
            return datetime.datetime.now(datetime.timezone.utc)
        try:
            return datetime.datetime.strptime(raw, "%Y-%m-%d").replace(
                tzinfo=datetime.timezone.utc
            )
        except (ValueError, AttributeError):
            return datetime.datetime.now(datetime.timezone.utc)
