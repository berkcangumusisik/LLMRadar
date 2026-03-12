from __future__ import annotations

import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class GeminiAnalysis(BaseModel):
    category_tags: list[str] = Field(default_factory=list, max_length=2)
    model_tags: list[str] = Field(default_factory=list, max_length=3)
    summary_en: str = ""
    summary_tr: str = ""
    importance: int = Field(default=5, ge=1, le=10)
    is_llm_related: bool = True
    key_metric: str = ""


class RawArticle(BaseModel):
    title: str
    content: str
    url: HttpUrl
    source: str
    author: str | None = None
    published_at: datetime.datetime


class ArticleOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    url: str
    source: str
    author: str | None = None
    category_tags: list[str] = []
    model_tags: list[str] = []
    summary_en: str | None = None
    summary_tr: str | None = None
    importance: int = 5
    key_metric: str | None = None
    is_llm_related: bool = True
    published_at: datetime.datetime
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class RelatedArticle(BaseModel):
    id: uuid.UUID
    title: str
    url: str
    source: str
    category_tags: list[str] = []
    model_tags: list[str] = []
    summary_tr: str | None = None
    summary_en: str | None = None
    importance: int = 5
    published_at: datetime.datetime
    similarity: float


class WSMessage(BaseModel):
    type: Literal["new_article", "search_results", "ping"]
    data: ArticleOut | list[ArticleOut] | None = None



class FeedResponse(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    page_size: int
    has_next: bool
