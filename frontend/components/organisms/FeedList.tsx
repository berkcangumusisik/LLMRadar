"use client";

import { FeedCard } from "./FeedCard";
import { SkeletonCard } from "@/components/molecules";
import { SKELETON_COUNT } from "@/lib/constants";
import { useLanguage } from "@/hooks/useLanguage";
import type { Article } from "@/lib/types";

interface FeedListProps {
  articles: Article[];
  isLoading: boolean;
  hasNext: boolean;
  onLoadMore: () => void;
  onRelatedClick: (article: Article) => void;
}

export function FeedList({
  articles,
  isLoading,
  hasNext,
  onLoadMore,
  onRelatedClick,
}: FeedListProps) {
  const { t } = useLanguage();

  if (isLoading && articles.length === 0) {
    return (
      <div className="grid gap-4">
        {Array.from({ length: SKELETON_COUNT }, (_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!isLoading && articles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <p className="text-lg font-medium text-zinc-400">
          {t("feed.empty.title")}
        </p>
        <p className="mt-1 text-sm text-zinc-600">
          {t("feed.empty.subtitle")}
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      {articles.map((article) => (
        <FeedCard
          key={article.id}
          article={article}
          onRelatedClick={onRelatedClick}
        />
      ))}

      {hasNext && (
        <button
          onClick={onLoadMore}
          disabled={isLoading}
          className="mx-auto rounded-xl border border-zinc-800 bg-zinc-900/60 px-6 py-2.5 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-zinc-800 disabled:opacity-50"
        >
          {isLoading ? t("feed.loading") : t("feed.loadMore")}
        </button>
      )}
    </div>
  );
}
