import { timeAgo } from "@/lib/utils";

interface TimeAgoProps {
  date: string;
}

export function TimeAgo({ date }: TimeAgoProps) {
  return (
    <time
      dateTime={date}
      className="text-xs text-zinc-500"
      title={new Date(date).toLocaleString()}
    >
      {timeAgo(date)}
    </time>
  );
}
