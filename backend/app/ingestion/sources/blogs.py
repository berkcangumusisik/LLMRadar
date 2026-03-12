from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET

from app.ingestion.sources.base import BaseSource
from app.models.schemas import RawArticle

RSS_FEEDS: dict[str, str] = {
    "openai": "https://openai.com/blog/rss",
    "anthropic": "https://anthropic.com/news/rss",
    "google_ai": "https://blog.google/technology/ai/rss/",
    "meta_ai": "https://ai.meta.com/blog/rss/",
}

ATOM_NS = "{http://www.w3.org/2005/Atom}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"


class BlogsSource(BaseSource):
    name = "blogs"
    timeout = 45.0

    async def fetch(self) -> list[RawArticle]:
        articles: list[RawArticle] = []

        for blog_name, feed_url in RSS_FEEDS.items():
            try:
                items = await self._parse_feed(blog_name, feed_url)
                articles.extend(items)
            except Exception as exc:
                from app.ingestion.sources.base import logger
                logger.warning("blogs/%s failed: %s", blog_name, exc)

        return articles

    async def _parse_feed(self, blog_name: str, url: str) -> list[RawArticle]:
        resp = await self._client.get(url)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        articles: list[RawArticle] = []

        # RSS 2.0 format
        for item in root.findall(".//item"):
            article = self._parse_rss_item(item, blog_name)
            if article:
                articles.append(article)

        # Atom format
        for entry in root.findall(f"{ATOM_NS}entry"):
            article = self._parse_atom_entry(entry, blog_name)
            if article:
                articles.append(article)

        return articles

    def _parse_rss_item(self, item: ET.Element, blog_name: str) -> RawArticle | None:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        content_encoded = (item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        author = (item.findtext("author") or item.findtext(f"{DC_NS}creator") or "").strip()

        if not title or not link:
            return None

        content = content_encoded or description or title

        return RawArticle(
            title=title,
            content=self._strip_html(content)[:3000],
            url=link,
            source=f"blog_{blog_name}",
            author=author or None,
            published_at=self._parse_rss_date(pub_date),
        )

    def _parse_atom_entry(self, entry: ET.Element, blog_name: str) -> RawArticle | None:
        title = (entry.findtext(f"{ATOM_NS}title") or "").strip()

        link = ""
        for lnk in entry.findall(f"{ATOM_NS}link"):
            href = lnk.get("href", "")
            if lnk.get("rel", "alternate") == "alternate" and href:
                link = href
                break
        if not link:
            for lnk in entry.findall(f"{ATOM_NS}link"):
                href = lnk.get("href", "")
                if href:
                    link = href
                    break

        content_el = entry.find(f"{ATOM_NS}content")
        summary_el = entry.find(f"{ATOM_NS}summary")
        content = ""
        if content_el is not None and content_el.text:
            content = content_el.text.strip()
        elif summary_el is not None and summary_el.text:
            content = summary_el.text.strip()

        author_el = entry.find(f"{ATOM_NS}author")
        author = ""
        if author_el is not None:
            author = (author_el.findtext(f"{ATOM_NS}name") or "").strip()

        updated = (entry.findtext(f"{ATOM_NS}updated") or entry.findtext(f"{ATOM_NS}published") or "").strip()

        if not title or not link:
            return None

        return RawArticle(
            title=title,
            content=self._strip_html(content or title)[:3000],
            url=link,
            source=f"blog_{blog_name}",
            author=author or None,
            published_at=self._parse_iso_date(updated),
        )

    @staticmethod
    def _strip_html(text: str) -> str:
        import re
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    @staticmethod
    def _parse_rss_date(raw: str) -> datetime.datetime:
        if not raw:
            return datetime.datetime.now(datetime.timezone.utc)
        from email.utils import parsedate_to_datetime
        try:
            return parsedate_to_datetime(raw)
        except (ValueError, TypeError):
            return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def _parse_iso_date(raw: str) -> datetime.datetime:
        if not raw:
            return datetime.datetime.now(datetime.timezone.utc)
        try:
            return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.datetime.now(datetime.timezone.utc)
