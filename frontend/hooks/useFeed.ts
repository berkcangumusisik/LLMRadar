"use client";

import { useCallback, useEffect, useState } from "react";
import { API_URL, PAGE_SIZE } from "@/lib/constants";
import type { Article, FeedResponse } from "@/lib/types";

interface UseFeedOptions {
  source?: string;
  category?: string;
  modelTag?: string;
  minImportance?: number;
}

interface UseFeedReturn {
  articles: Article[];
  isLoading: boolean;
  error: string | null;
  hasNext: boolean;
  total: number;
  page: number;
  loadMore: () => void;
  refresh: () => void;
  prependArticle: (article: Article) => void;
}

export function useFeed(options: UseFeedOptions = {}): UseFeedReturn {
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [total, setTotal] = useState(0);

  const fetchPage = useCallback(
    async (pageNum: number, append: boolean) => {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: String(pageNum),
        page_size: String(PAGE_SIZE),
      });

      if (options.source) params.set("source", options.source);
      if (options.category) params.set("category", options.category);
      if (options.modelTag) params.set("model_tag", options.modelTag);
      if (options.minImportance)
        params.set("min_importance", String(options.minImportance));

      try {
        const res = await fetch(`${API_URL}/api/feed?${params}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: FeedResponse = await res.json();

        setArticles((prev) => (append ? [...prev, ...data.items] : data.items));
        setHasNext(data.has_next);
        setTotal(data.total);
        setPage(data.page);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch feed");
      } finally {
        setIsLoading(false);
      }
    },
    [options.source, options.category, options.modelTag, options.minImportance],
  );

  useEffect(() => {
    fetchPage(1, false);
  }, [fetchPage]);

  const loadMore = useCallback(() => {
    if (hasNext && !isLoading) {
      fetchPage(page + 1, true);
    }
  }, [hasNext, isLoading, page, fetchPage]);

  const refresh = useCallback(() => {
    fetchPage(1, false);
  }, [fetchPage]);

  const prependArticle = useCallback((article: Article) => {
    setArticles((prev) => {
      if (prev.some((a) => a.id === article.id)) return prev;
      return [article, ...prev];
    });
    setTotal((t) => t + 1);
  }, []);

  return {
    articles,
    isLoading,
    error,
    hasNext,
    total,
    page,
    loadMore,
    refresh,
    prependArticle,
  };
}
