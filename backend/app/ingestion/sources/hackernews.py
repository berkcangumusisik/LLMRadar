from __future__ import annotations

import asyncio
import datetime

from app.ingestion.sources.base import BaseSource, logger
from app.models.schemas import RawArticle

HN_TOP = "https://hacker-news.firebaseio.com/v0/newstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"

LLM_KEYWORDS = [
    "llm", "gpt", "claude", "gemini", "llama", "mistral", "deepseek",
    "openai", "anthropic", "transformer", "language model", "fine-tun",
    "rlhf", "rag", "multimodal", "benchmark", "reasoning", "agent",
    "chatbot", "token", "embedding", "diffusion", "hugging face",
    "open source ai", "ai safety", "alignment", "grok", "phi-",
    "qwen", "command r", "sora", "dall-e",
]

MAX_STORIES = 60
CONCURRENCY = 10


def _is_relevant(title: str, text: str) -> bool:
    combined = f"{title} {text}".lower()
    return any(kw in combined for kw in LLM_KEYWORDS)


class HackerNewsSource(BaseSource):
    name = "hackernews"

    async def fetch(self) -> list[RawArticle]:
        resp = await self._client.get(HN_TOP)
        resp.raise_for_status()
        story_ids: list[int] = resp.json()[:MAX_STORIES]

        sem = asyncio.Semaphore(CONCURRENCY)

        async def _get_item(sid: int) -> dict | None:
            async with sem:
                try:
                    r = await self._client.get(HN_ITEM.format(id=sid))
                    r.raise_for_status()
                    return r.json()
                except Exception:
                    return None

        results = await asyncio.gather(*[_get_item(sid) for sid in story_ids])

        articles: list[RawArticle] = []
        for item in results:
            if not item or item.get("type") != "story":
                continue

            title = item.get("title", "")
            text = item.get("text", "") or ""
            url = item.get("url", "")

            if not _is_relevant(title, text):
                continue

            published_at = datetime.datetime.fromtimestamp(
                item.get("time", 0),
                tz=datetime.timezone.utc,
            )
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
            if published_at < cutoff:
                continue

            if not url:
                url = f"https://news.ycombinator.com/item?id={item['id']}"

            content = text if text else title
            author = item.get("by")

            articles.append(
                RawArticle(
                    title=title,
                    content=content,
                    url=url,
                    source="hackernews",
                    author=author,
                    published_at=published_at,
                )
            )

        return articles
