from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET

from app.ingestion.sources.base import BaseSource
from app.models.schemas import RawArticle

ARXIV_API = "http://export.arxiv.org/api/query"

CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"]

LLM_KEYWORDS = [
    "large language model",
    "LLM",
    "GPT",
    "transformer",
    "RLHF",
    "instruction tuning",
    "fine-tuning",
    "prompt",
    "reasoning",
    "alignment",
    "multimodal",
    "retrieval augmented",
    "RAG",
    "agent",
    "benchmark",
    "tokenizer",
    "diffusion",
    "text generation",
]

ATOM_NS = "{http://www.w3.org/2005/Atom}"


class ArxivSource(BaseSource):
    name = "arxiv"
    timeout = 60.0

    async def fetch(self) -> list[RawArticle]:
        cat_query = " OR ".join(f"cat:{c}" for c in CATEGORIES)
        kw_query = " OR ".join(f'all:"{k}"' for k in LLM_KEYWORDS[:8])
        search_query = f"({cat_query}) AND ({kw_query})"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": 40,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        resp = await self._client.get(ARXIV_API, params=params)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        articles: list[RawArticle] = []

        for entry in root.findall(f"{ATOM_NS}entry"):
            title = (entry.findtext(f"{ATOM_NS}title") or "").strip().replace("\n", " ")
            summary = (entry.findtext(f"{ATOM_NS}summary") or "").strip().replace("\n", " ")
            link = ""
            for lnk in entry.findall(f"{ATOM_NS}link"):
                if lnk.get("type") == "text/html":
                    link = lnk.get("href", "")
                    break
            if not link:
                link = (entry.findtext(f"{ATOM_NS}id") or "").strip()

            published_raw = (entry.findtext(f"{ATOM_NS}published") or "").strip()
            if not published_raw:
                continue

            published_at = datetime.datetime.fromisoformat(
                published_raw.replace("Z", "+00:00")
            )

            authors: list[str] = []
            for author_el in entry.findall(f"{ATOM_NS}author"):
                name = (author_el.findtext(f"{ATOM_NS}name") or "").strip()
                if name:
                    authors.append(name)

            if not title or not link:
                continue

            articles.append(
                RawArticle(
                    title=title,
                    content=summary or title,
                    url=link,
                    source="arxiv",
                    author=", ".join(authors[:3]) if authors else None,
                    published_at=published_at,
                )
            )

        return articles
