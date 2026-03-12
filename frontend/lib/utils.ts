import { CATEGORY_COLORS, SOURCE_LABELS } from "./constants";
import type { CategoryTag } from "./types";

export function getCategoryColor(tag: string): string {
  return CATEGORY_COLORS[tag as CategoryTag] ?? "#6B7280";
}

export function getSourceLabel(source: string): string {
  if (SOURCE_LABELS[source]) return SOURCE_LABELS[source];
  if (source.startsWith("x_")) return `@${source.slice(2)}`;
  if (source.startsWith("blog_")) return source.slice(5).replace(/_/g, " ");
  return source;
}

export function timeAgo(dateString: string): string {
  const now = Date.now();
  const then = new Date(dateString).getTime();
  const diff = Math.max(0, now - then);

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return "just now";
}

export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen).trimEnd() + "…";
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function importanceLabel(importance: number): string {
  if (importance >= 9) return "Breaking";
  if (importance >= 7) return "Important";
  if (importance >= 5) return "Notable";
  return "Minor";
}
