"use client";

import { useCallback, useEffect, useState } from "react";
import { X } from "lucide-react";
import { IconButton } from "@/components/atoms";
import { RelatedItem } from "@/components/molecules";
import { API_URL } from "@/lib/constants";
import { useLanguage } from "@/hooks/useLanguage";
import type { Article, RelatedArticle } from "@/lib/types";

interface RelatedDrawerProps {
  article: Article | null;
  onClose: () => void;
}

export function RelatedDrawer({ article, onClose }: RelatedDrawerProps) {
  const { t } = useLanguage();
  const [related, setRelated] = useState<RelatedArticle[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchRelated = useCallback(async (id: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/articles/${id}/related`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: RelatedArticle[] = await res.json();
      setRelated(data);
    } catch {
      setRelated([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (article) {
      fetchRelated(article.id);
    } else {
      setRelated([]);
    }
  }, [article, fetchRelated]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!article) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      <aside className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col border-l border-zinc-800 bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-800 px-5 py-4">
          <h2 className="text-sm font-semibold text-zinc-200">
            {t("related.title")}
          </h2>
          <IconButton label={t("related.close")} onClick={onClose}>
            <X size={18} />
          </IconButton>
        </div>

        <div className="border-b border-zinc-800 px-5 py-3">
          <p className="text-sm font-medium leading-snug text-zinc-300">
            {article.title}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {isLoading && (
            <p className="py-8 text-center text-sm text-zinc-500">
              {t("related.loading")}
            </p>
          )}

          {!isLoading && related.length === 0 && (
            <p className="py-8 text-center text-sm text-zinc-500">
              {t("related.empty")}
            </p>
          )}

          {!isLoading && related.length > 0 && (
            <div className="grid gap-3">
              {related.map((item) => (
                <RelatedItem key={item.id} article={item} />
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
