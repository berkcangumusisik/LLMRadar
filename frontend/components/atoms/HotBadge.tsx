import { Flame } from "lucide-react";

interface HotBadgeProps {
  importance: number;
  label?: string;
}

export function HotBadge({ importance, label = "HOT" }: HotBadgeProps) {
  if (importance < 8) return null;

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-red-500/15 px-2 py-0.5 text-xs font-bold text-red-400">
      <Flame size={12} />
      {label}
    </span>
  );
}
