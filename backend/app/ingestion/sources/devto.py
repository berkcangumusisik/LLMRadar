from __future__ import annotations

import datetime

from app.ingestion.sources.base import BaseSource, logger
from app.models.schemas import RawArticle

DEVTO_API = "https://dev.to/api/articles"

TAGS = ["ai", "machinelearning", "llm", "openai", "nlp"]


class DevToSource(BaseSource):
    name = "devto"
    timeout = 30.0

    async def fetch(self) -> list[RawArticle]:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=48)
        articles: list[RawArticle] = []
        seen_urls: set[str] = set()

        for tag in TAGS:
            try:
                items = await self._fetch_tag(tag, cutoff, seen_urls)
                articles.extend(items)
            except Exception as exc:
                logger.warning("devto/%s failed: %s", tag, exc)

        return articles

    async def _fetch_tag(
        self, tag: str, cutoff: datetime.datetime, seen_urls: set[str]
    ) -> list[RawArticle]:
        params = {"tag": tag, "per_page": 15, "state": "rising"}
        resp = await self._client.get(DEVTO_API, params=params)
        resp.raise_for_status()
        data = resp.json()

        articles: list[RawArticle] = []
        for item in data:
            title = (item.get("title") or "").strip()
            description = (item.get("description") or "").strip()
            url = (item.get("url") or "").strip()
            published_raw = item.get("published_at", "")
            user = item.get("user", {})
            author = user.get("name") or user.get("username")

            if not title or not url:
                continue

            if url in seen_urls:
                continue
            seen_urls.add(url)

            published_at = self._parse_date(published_raw)
            if published_at < cutoff:
                continue

            tag_list = item.get("tag_list", [])
            content = description or title
            if tag_list:
                content = f"{content} [{', '.join(tag_list)}]"

            articles.append(
                RawArticle(
                    title=title,
                    content=content[:3000],
                    url=url,
                    source="devto",
                    author=author,
                    published_at=published_at,
                )
            )

        return articles

    @staticmethod
    def _parse_date(raw: str) -> datetime.datetime:
        if not raw:
            return datetime.datetime.now(datetime.timezone.utc)
        try:
            return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.datetime.now(datetime.timezone.utc)
