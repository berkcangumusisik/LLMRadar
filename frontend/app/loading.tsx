import { SkeletonCard } from "@/components/molecules";
import { SKELETON_COUNT } from "@/lib/constants";

export default function Loading() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-center gap-3">
        <div className="h-10 w-10 animate-pulse rounded-xl bg-zinc-800" />
        <div className="space-y-1.5">
          <div className="h-5 w-32 animate-pulse rounded bg-zinc-800" />
          <div className="h-3 w-48 animate-pulse rounded bg-zinc-800" />
        </div>
      </div>
      <div className="grid gap-4">
        {Array.from({ length: SKELETON_COUNT }, (_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </div>
  );
}
