from __future__ import annotations

import datetime

from app.ingestion.sources.base import BaseSource, logger
from app.models.schemas import RawArticle

PWC_API = "https://paperswithcode.com/api/v1/papers/"


class PapersWithCodeSource(BaseSource):
    name = "paperswithcode"
    timeout = 30.0

    async def fetch(self) -> list[RawArticle]:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=48)

        params = {"ordering": "-published", "page": 1, "items_per_page": 30}
        resp = await self._client.get(PWC_API, params=params)
        resp.raise_for_status()
        data = resp.json()

        articles: list[RawArticle] = []
        for item in data.get("results", []):
            title = (item.get("title") or "").strip()
            abstract = (item.get("abstract") or "").strip()
            url_pdf = item.get("url_pdf", "")
            url_abs = item.get("url_abs", "")
            published_raw = item.get("published", "")

            if not title:
                continue

            url = url_abs or url_pdf
            if not url:
                continue

            published_at = self._parse_date(published_raw)
            if published_at < cutoff:
                continue

            authors_list = item.get("authors", [])
            author_str = ", ".join(authors_list[:3]) if authors_list else None

            articles.append(
                RawArticle(
                    title=title,
                    content=abstract or title,
                    url=url,
                    source="paperswithcode",
                    author=author_str,
                    published_at=published_at,
                )
            )

        logger.info("paperswithcode: %d articles after 48h filter", len(articles))
        return articles

    @staticmethod
    def _parse_date(raw: str) -> datetime.datetime:
        if not raw:
            return datetime.datetime.now(datetime.timezone.utc)
        try:
            return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            try:
                return datetime.datetime.strptime(raw, "%Y-%m-%d").replace(
                    tzinfo=datetime.timezone.utc
                )
            except ValueError:
                return datetime.datetime.now(datetime.timezone.utc)
