from __future__ import annotations

import datetime

from app.ingestion.sources.base import BaseSource
from app.models.schemas import RawArticle

HF_PAPERS_API = "https://huggingface.co/api/daily_papers"
HF_TRENDING_API = "https://huggingface.co/api/trending"


class HuggingFaceSource(BaseSource):
    name = "huggingface"

    async def fetch(self) -> list[RawArticle]:
        articles: list[RawArticle] = []

        papers = await self._fetch_papers()
        articles.extend(papers)

        trending = await self._fetch_trending()
        articles.extend(trending)

        return articles

    async def _fetch_papers(self) -> list[RawArticle]:
        resp = await self._client.get(HF_PAPERS_API)
        resp.raise_for_status()
        data = resp.json()

        articles: list[RawArticle] = []
        for item in data:
            paper = item.get("paper", {})
            title = paper.get("title", "").strip()
            summary = paper.get("summary", "").strip()
            paper_id = paper.get("id", "")

            if not title or not paper_id:
                continue

            url = f"https://huggingface.co/papers/{paper_id}"

            published_raw = paper.get("publishedAt") or item.get("publishedAt", "")
            published_at = self._parse_date(published_raw)

            authors: list[str] = []
            for a in paper.get("authors", []):
                name = a.get("name", "").strip()
                if name:
                    authors.append(name)

            articles.append(
                RawArticle(
                    title=title,
                    content=summary or title,
                    url=url,
                    source="huggingface",
                    author=", ".join(authors[:3]) if authors else None,
                    published_at=published_at,
                )
            )

        return articles

    async def _fetch_trending(self) -> list[RawArticle]:
        try:
            resp = await self._client.get(HF_TRENDING_API)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        articles: list[RawArticle] = []
        recently_trending = data.get("recentlyTrending", [])

        for item in recently_trending[:20]:
            repo_id = item.get("repoData", {}).get("id", "")
            if not repo_id:
                continue

            title = f"Trending: {repo_id}"
            description = item.get("repoData", {}).get("description", "") or ""
            url = f"https://huggingface.co/{repo_id}"
            author = repo_id.split("/")[0] if "/" in repo_id else None

            articles.append(
                RawArticle(
                    title=title,
                    content=description or title,
                    url=url,
                    source="huggingface",
                    author=author,
                    published_at=datetime.datetime.now(datetime.timezone.utc),
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
