from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET

from app.core.config import get_settings
from app.ingestion.sources.base import BaseSource, logger
from app.models.schemas import RawArticle


class RSSHubSource(BaseSource):
    name = "rsshub"
    timeout = 30.0

    async def fetch(self) -> list[RawArticle]:
        settings = get_settings()
        articles: list[RawArticle] = []

        for account in settings.X_ACCOUNTS:
            items = await self._fetch_account(account, settings)
            articles.extend(items)

        return articles

    async def _fetch_account(
        self, account: str, settings: object
    ) -> list[RawArticle]:
        primary_url = f"{settings.RSSHUB_BASE_URL}/twitter/user/{account}"
        fallback_url = f"{settings.NITTER_BASE_URL}/{account}/rss"

        for url in (primary_url, fallback_url):
            try:
                resp = await self._client.get(url)
                resp.raise_for_status()
                return self._parse_rss(resp.text, account)
            except Exception as exc:
                logger.debug("rsshub/%s failed on %s: %s", account, url, exc)
                continue

        logger.warning("rsshub/%s: all endpoints failed", account)
        return []

    def _parse_rss(self, xml_text: str, account: str) -> list[RawArticle]:
        root = ET.fromstring(xml_text)
        articles: list[RawArticle] = []

        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()

            if not title and not description:
                continue

            content = self._strip_html(description or title)
            if not link:
                continue

            articles.append(
                RawArticle(
                    title=title or content[:120],
                    content=content[:2000],
                    url=link,
                    source=f"x_{account}",
                    author=f"@{account}",
                    published_at=self._parse_rss_date(pub_date),
                )
            )

        return articles

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
