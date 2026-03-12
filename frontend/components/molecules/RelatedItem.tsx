import { SourceIcon, TimeAgo } from "@/components/atoms";
import { getSourceLabel, truncate } from "@/lib/utils";
import type { RelatedArticle } from "@/lib/types";

interface RelatedItemProps {
  article: RelatedArticle;
}

export function RelatedItem({ article }: RelatedItemProps) {
  const similarity = Math.round(article.similarity * 100);

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block rounded-lg border border-zinc-800 p-3 transition-colors hover:border-zinc-700 hover:bg-zinc-800/50"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <SourceIcon source={article.source} size={14} />
          <span className="text-xs text-zinc-500">
            {getSourceLabel(article.source)}
          </span>
        </div>
        <span className="shrink-0 rounded-full bg-violet-500/15 px-2 py-0.5 text-xs font-medium text-violet-400">
          {similarity}%
        </span>
      </div>
      <p className="mt-1.5 text-sm font-medium leading-snug text-zinc-200">
        {truncate(article.title, 100)}
      </p>
      <div className="mt-1.5">
        <TimeAgo date={article.published_at} />
      </div>
    </a>
  );
}
