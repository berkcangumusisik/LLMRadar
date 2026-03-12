import {
  BookOpen,
  Globe,
  MessageSquare,
  Newspaper,
  Twitter,
} from "lucide-react";
import type { ComponentType } from "react";

interface SourceIconProps {
  source: string;
  size?: number;
}

const iconMap: Record<string, ComponentType<{ size?: number; className?: string }>> = {
  arxiv: BookOpen,
  hackernews: MessageSquare,
  huggingface: Globe,
};

export function SourceIcon({ source, size = 16 }: SourceIconProps) {
  if (source.startsWith("x_")) {
    return <Twitter size={size} className="text-zinc-400" />;
  }
  if (source.startsWith("blog_")) {
    return <Newspaper size={size} className="text-zinc-400" />;
  }
  const Icon = iconMap[source] ?? Globe;
  return <Icon size={size} className="text-zinc-400" />;
}
