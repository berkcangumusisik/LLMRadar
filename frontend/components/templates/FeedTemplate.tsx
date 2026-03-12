"use client";

import { useCallback, useState } from "react";
import { FeedHeader, FeedList, RelatedDrawer, SearchBar } from "@/components/organisms";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useFeed } from "@/hooks/useFeed";
import { useSearch } from "@/hooks/useSearch";
import type { Article } from "@/lib/types";
import { useEffect } from "react";

export function FeedTemplate() {
  const { isConnected, lastArticle, searchResults, sendSearch } = useWebSocket();
  const feed = useFeed();
  const search = useSearch(sendSearch, searchResults);
  const [drawerArticle, setDrawerArticle] = useState<Article | null>(null);

  useEffect(() => {
    if (lastArticle) {
      feed.prependArticle(lastArticle);
    }
  }, [lastArticle]);  // eslint-disable-line react-hooks/exhaustive-deps

  const handleRelatedClick = useCallback((article: Article) => {
    setDrawerArticle(article);
  }, []);

  const handleDrawerClose = useCallback(() => {
    setDrawerArticle(null);
  }, []);

  const isSearchActive = search.query.length >= 2;

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="space-y-6">
        <FeedHeader
          isConnected={isConnected}
          totalArticles={feed.total}
        />

        <SearchBar
          query={search.query}
          onQueryChange={search.setQuery}
          onClear={search.clearSearch}
          results={search.results}
          isSearching={search.isSearching}
          onRelatedClick={handleRelatedClick}
        />

        {!isSearchActive && (
          <FeedList
            articles={feed.articles}
            isLoading={feed.isLoading}
            hasNext={feed.hasNext}
            onLoadMore={feed.loadMore}
            onRelatedClick={handleRelatedClick}
          />
        )}
      </div>

      <RelatedDrawer
        article={drawerArticle}
        onClose={handleDrawerClose}
      />
    </div>
  );
}
