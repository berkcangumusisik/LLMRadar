"use client";

import { ExternalLink, Link2 } from "lucide-react";
import { IconButton } from "@/components/atoms";
import { CardHeader, SummaryToggle, TagGroup } from "@/components/molecules";
import { truncate } from "@/lib/utils";
import { useLanguage } from "@/hooks/useLanguage";
import type { Article } from "@/lib/types";

interface FeedCardProps {
  article: Article;
  onRelatedClick: (article: Article) => void;
}

export function FeedCard({ article, onRelatedClick }: FeedCardProps) {
  const { t } = useLanguage();

  return (
    <article className="group rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 transition-colors hover:border-zinc-700">
      <CardHeader
        source={article.source}
        publishedAt={article.published_at}
        importance={article.importance}
        author={article.author}
        hotLabel={t("hot.label")}
      />

      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-3 block"
      >
        <h3 className="text-base font-semibold leading-snug text-zinc-100 transition-colors group-hover:text-white">
          {truncate(article.title, 140)}
        </h3>
      </a>

      <div className="mt-2.5">
        <TagGroup
          categoryTags={article.category_tags}
          modelTags={article.model_tags}
          keyMetric={article.key_metric}
        />
      </div>

      <div className="mt-3">
        <SummaryToggle
          summaryTr={article.summary_tr}
          summaryEn={article.summary_en}
        />
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-zinc-800/60 pt-3">
        <div className="flex items-center gap-1">
          <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs font-medium text-zinc-400">
            {t("card.importance", { score: article.importance })}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <IconButton
            label={t("card.related")}
            onClick={() => onRelatedClick(article)}
          >
            <Link2 size={15} />
          </IconButton>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={t("card.openOriginal")}
            className="inline-flex items-center justify-center rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-100"
          >
            <ExternalLink size={15} />
          </a>
        </div>
      </div>
    </article>
  );
}
