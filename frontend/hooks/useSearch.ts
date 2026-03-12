"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Article } from "@/lib/types";

interface UseSearchReturn {
  query: string;
  setQuery: (q: string) => void;
  results: Article[];
  isSearching: boolean;
  clearSearch: () => void;
}

export function useSearch(
  sendSearch: (query: string) => void,
  wsResults: Article[],
): UseSearchReturn {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<Article[]>([]);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (wsResults.length > 0 || query === "") {
      setResults(wsResults);
      setIsSearching(false);
    }
  }, [wsResults, query]);

  const handleQuery = useCallback(
    (q: string) => {
      setQuery(q);
      debounceRef.current && clearTimeout(debounceRef.current);

      if (q.trim().length < 2) {
        setResults([]);
        setIsSearching(false);
        return;
      }

      setIsSearching(true);
      debounceRef.current = setTimeout(() => {
        sendSearch(q.trim());
      }, 350);
    },
    [sendSearch],
  );

  const clearSearch = useCallback(() => {
    setQuery("");
    setResults([]);
    setIsSearching(false);
  }, []);

  return {
    query,
    setQuery: handleQuery,
    results,
    isSearching,
    clearSearch,
  };
}
