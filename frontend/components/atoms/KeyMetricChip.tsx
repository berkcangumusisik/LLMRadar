import { TrendingUp } from "lucide-react";

interface KeyMetricChipProps {
  metric: string;
}

export function KeyMetricChip({ metric }: KeyMetricChipProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs font-semibold text-amber-400">
      <TrendingUp size={12} />
      {metric}
    </span>
  );
}
