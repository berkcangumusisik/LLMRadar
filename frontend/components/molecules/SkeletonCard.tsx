import { SkeletonLine } from "@/components/atoms";

export function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-3">
      <div className="flex items-center justify-between">
        <SkeletonLine width="30%" height="0.75rem" />
        <SkeletonLine width="15%" height="0.75rem" />
      </div>
      <SkeletonLine width="85%" height="1.25rem" />
      <div className="flex gap-2">
        <SkeletonLine width="4.5rem" height="1.25rem" />
        <SkeletonLine width="3.5rem" height="1.25rem" />
      </div>
      <SkeletonLine width="100%" height="0.75rem" />
      <SkeletonLine width="70%" height="0.75rem" />
    </div>
  );
}
