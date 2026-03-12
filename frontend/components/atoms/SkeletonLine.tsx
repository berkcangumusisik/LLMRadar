interface SkeletonLineProps {
  width?: string;
  height?: string;
}

export function SkeletonLine({ width = "100%", height = "0.75rem" }: SkeletonLineProps) {
  return (
    <div
      className="animate-pulse rounded bg-zinc-800"
      style={{ width, height }}
    />
  );
}
