interface LiveBadgeProps {
  isConnected: boolean;
  connectedText?: string;
  disconnectedText?: string;
}

export function LiveBadge({
  isConnected,
  connectedText = "LIVE",
  disconnectedText = "OFFLINE",
}: LiveBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium">
      <span
        className={`h-2 w-2 rounded-full ${
          isConnected
            ? "animate-pulse bg-emerald-500"
            : "bg-zinc-500"
        }`}
      />
      <span className={isConnected ? "text-emerald-400" : "text-zinc-500"}>
        {isConnected ? connectedText : disconnectedText}
      </span>
    </span>
  );
}
