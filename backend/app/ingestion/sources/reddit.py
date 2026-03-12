from __future__ import annotations

import datetime

from app.ingestion.sources.base import BaseSource, logger
from app.models.schemas import RawArticle

SUBREDDITS = [
    "MachineLearning",
    "LocalLLaMA",
    "artificial",
]

LLM_KEYWORDS = [
    "llm", "gpt", "claude", "gemini", "llama", "mistral", "deepseek",
    "openai", "anthropic", "transformer", "language model", "fine-tun",
    "rlhf", "rag", "multimodal", "benchmark", "reasoning", "agent",
    "embedding", "hugging face", "open source ai", "alignment",
    "grok", "qwen", "phi", "sora",
]


def _is_relevant(title: str, selftext: str) -> bool:
    combined = f"{title} {selftext}".lower()
    return any(kw in combined for kw in LLM_KEYWORDS)


class RedditSource(BaseSource):
    name = "reddit"
    timeout = 30.0

    async def fetch(self) -> list[RawArticle]:
        articles: list[RawArticle] = []
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)

        for sub in SUBREDDITS:
            try:
                items = await self._fetch_subreddit(sub, cutoff)
                articles.extend(items)
            except Exception as exc:
                logger.warning("reddit/%s failed: %s", sub, exc)

        return articles

    async def _fetch_subreddit(
        self, subreddit: str, cutoff: datetime.datetime
    ) -> list[RawArticle]:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=30"
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()

        articles: list[RawArticle] = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = post.get("title", "").strip()
            selftext = post.get("selftext", "").strip()
            permalink = post.get("permalink", "")
            created_utc = post.get("created_utc", 0)
            author = post.get("author", "")
            ext_url = post.get("url", "")

            if not title:
                continue

            published_at = datetime.datetime.fromtimestamp(
                created_utc, tz=datetime.timezone.utc
            )
            if published_at < cutoff:
                continue

            if not _is_relevant(title, selftext):
                continue

            article_url = f"https://www.reddit.com{permalink}"
            content = selftext[:3000] if selftext else title

            if ext_url and "reddit.com" not in ext_url:
                content = f"{content}\n\nLink: {ext_url}"

            articles.append(
                RawArticle(
                    title=title,
                    content=content,
                    url=article_url,
                    source=f"reddit_{subreddit}",
                    author=f"u/{author}" if author else None,
                    published_at=published_at,
                )
            )

        return articles
