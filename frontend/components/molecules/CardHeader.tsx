import { HotBadge, SourceIcon, TimeAgo } from "@/components/atoms";
import { getSourceLabel } from "@/lib/utils";

interface CardHeaderProps {
  source: string;
  publishedAt: string;
  importance: number;
  author: string | null;
  hotLabel?: string;
}

export function CardHeader({ source, publishedAt, importance, author, hotLabel }: CardHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <SourceIcon source={source} />
        <span className="text-xs font-medium text-zinc-400">
          {getSourceLabel(source)}
        </span>
        {author && (
          <span className="text-xs text-zinc-600">
            · {author}
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <HotBadge importance={importance} label={hotLabel} />
        <TimeAgo date={publishedAt} />
      </div>
    </div>
  );
}
