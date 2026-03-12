import type { CategoryTag } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export const CATEGORY_COLORS: Record<CategoryTag, string> = {
  "Model Release": "#7C3AED",
  Benchmark: "#2563EB",
  Research: "#16A34A",
  "Safety & Alignment": "#DC2626",
  "API & Pricing": "#EA580C",
  "Company News": "#4B5563",
  "Open Source": "#65A30D",
  Multimodal: "#DB2777",
  "Fine-tuning": "#CA8A04",
  "Agentic AI": "#4F46E5",
  Regulation: "#92400E",
};

export const SOURCE_LABELS: Record<string, string> = {
  arxiv: "arXiv",
  hackernews: "Hacker News",
  huggingface: "Hugging Face",
  blog_google_ai: "Google AI Blog",
  blog_techcrunch_ai: "TechCrunch AI",
  blog_theverge_ai: "The Verge AI",
  blog_venturebeat_ai: "VentureBeat AI",
  blog_arstechnica: "Ars Technica",
  reddit_MachineLearning: "r/MachineLearning",
  reddit_LocalLLaMA: "r/LocalLLaMA",
  reddit_artificial: "r/artificial",
  paperswithcode: "Papers With Code",
  devto: "Dev.to",
  github_trending: "GitHub Trending",
  semanticscholar: "Semantic Scholar",
};

export const SKELETON_COUNT = 12;

export const WS_PING_INTERVAL = 30_000;

export const PAGE_SIZE = 20;
