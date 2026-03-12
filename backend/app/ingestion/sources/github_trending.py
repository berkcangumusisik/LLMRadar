from __future__ import annotations

import datetime
import re

from app.ingestion.sources.base import BaseSource, logger
from app.models.schemas import RawArticle

GITHUB_TRENDING_URL = "https://github.com/trending"


class GitHubTrendingSource(BaseSource):
    name = "github_trending"
    timeout = 30.0

    async def fetch(self) -> list[RawArticle]:
        articles: list[RawArticle] = []

        for lang in ["python", ""]:
            try:
                items = await self._fetch_page(lang)
                articles.extend(items)
            except Exception as exc:
                logger.warning("github_trending/%s failed: %s", lang or "all", exc)

        seen: set[str] = set()
        unique: list[RawArticle] = []
        for a in articles:
            if str(a.url) not in seen:
                seen.add(str(a.url))
                unique.append(a)

        return unique

    async def _fetch_page(self, language: str) -> list[RawArticle]:
        params: dict[str, str] = {"since": "daily"}
        if language:
            params["spoken_language_code"] = ""
            url = f"{GITHUB_TRENDING_URL}/{language}"
        else:
            url = GITHUB_TRENDING_URL

        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        html = resp.text

        return self._parse_html(html)

    def _parse_html(self, html: str) -> list[RawArticle]:
        ai_keywords = [
            "llm", "gpt", "transformer", "language-model", "langchain",
            "ai", "ml", "deep-learning", "neural", "embedding",
            "rag", "fine-tun", "diffusion", "agent", "huggingface",
            "openai", "anthropic", "gemini", "llama", "mistral",
        ]

        articles: list[RawArticle] = []
        repo_blocks = re.findall(
            r'<article class="Box-row">(.*?)</article>', html, re.DOTALL
        )

        for block in repo_blocks:
            repo_match = re.search(r'href="(/[^"]+)"', block)
            if not repo_match:
                continue

            repo_path = repo_match.group(1).strip()
            repo_name = repo_path.lstrip("/")
            url = f"https://github.com{repo_path}"

            desc_match = re.search(r'<p class="[^"]*">(.*?)</p>', block, re.DOTALL)
            description = ""
            if desc_match:
                description = re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()

            combined = f"{repo_name} {description}".lower()
            if not any(kw in combined for kw in ai_keywords):
                continue

            stars_match = re.search(
                r'(\d[\d,]*)\s*stars?\s*today', block, re.IGNORECASE
            )
            stars_today = ""
            if stars_match:
                stars_today = stars_match.group(1).replace(",", "")

            title = repo_name
            content = description or repo_name
            if stars_today:
                content = f"{content} ({stars_today} stars today)"

            author = repo_name.split("/")[0] if "/" in repo_name else None

            articles.append(
                RawArticle(
                    title=f"Trending: {title}",
                    content=content[:2000],
                    url=url,
                    source="github_trending",
                    author=author,
                    published_at=datetime.datetime.now(datetime.timezone.utc),
                )
            )

        logger.info("github_trending: %d AI repos found", len(articles))
        return articles
