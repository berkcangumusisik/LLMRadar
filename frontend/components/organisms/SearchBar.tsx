"use client";

import { FeedCard } from "./FeedCard";
import { SearchInput } from "@/components/molecules";
import { useLanguage } from "@/hooks/useLanguage";
import type { Article } from "@/lib/types";

interface SearchBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  onClear: () => void;
  results: Article[];
  isSearching: boolean;
  onRelatedClick: (article: Article) => void;
}

export function SearchBar({
  query,
  onQueryChange,
  onClear,
  results,
  isSearching,
  onRelatedClick,
}: SearchBarProps) {
  const { t } = useLanguage();

  return (
    <div className="space-y-4">
      <SearchInput
        value={query}
        onChange={onQueryChange}
        onClear={onClear}
        placeholder={t("search.placeholder")}
        clearLabel={t("search.clear")}
      />

      {query.length >= 2 && (
        <div>
          {isSearching && (
            <p className="py-4 text-center text-sm text-zinc-500">
              {t("search.searching")}
            </p>
          )}

          {!isSearching && results.length === 0 && (
            <p className="py-4 text-center text-sm text-zinc-500">
              {t("search.noResults", { query })}
            </p>
          )}

          {!isSearching && results.length > 0 && (
            <div className="grid gap-4">
              <p className="text-xs font-medium text-zinc-500">
                {t("search.resultCount", {
                  count: results.length,
                  plural: results.length !== 1 ? "s" : "",
                })}
              </p>
              {results.map((article) => (
                <FeedCard
                  key={article.id}
                  article={article}
                  onRelatedClick={onRelatedClick}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
