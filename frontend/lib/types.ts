export interface Article {
  id: string;
  title: string;
  content: string;
  url: string;
  source: string;
  author: string | null;
  category_tags: string[];
  model_tags: string[];
  summary_en: string | null;
  summary_tr: string | null;
  importance: number;
  key_metric: string | null;
  is_llm_related: boolean;
  published_at: string;
  created_at: string;
}

export interface RelatedArticle {
  id: string;
  title: string;
  url: string;
  source: string;
  category_tags: string[];
  model_tags: string[];
  summary_tr: string | null;
  summary_en: string | null;
  importance: number;
  published_at: string;
  similarity: number;
}

export interface FeedResponse {
  items: Article[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface WSMessage {
  type: "new_article" | "search_results" | "ping";
  data: Article | Article[] | null;
}

export type CategoryTag =
  | "Model Release"
  | "Benchmark"
  | "Research"
  | "Safety & Alignment"
  | "API & Pricing"
  | "Company News"
  | "Open Source"
  | "Multimodal"
  | "Fine-tuning"
  | "Agentic AI"
  | "Regulation";

export type ModelTag =
  | "GPT"
  | "Claude"
  | "Gemini"
  | "Llama"
  | "Mistral"
  | "DeepSeek"
  | "Grok"
  | "Qwen"
  | "Command R"
  | "Phi"
  | "Sora"
  | "DALL-E";
