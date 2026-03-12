export type Locale = "tr" | "en";

const translations = {
  // Header
  "header.subtitle.tracking": {
    tr: "{count} haber takip ediliyor",
    en: "{count} articles tracked",
  },
  "header.subtitle.default": {
    tr: "Gerçek zamanlı LLM haber akışı",
    en: "Real-time LLM news aggregator",
  },

  // LiveBadge
  "live.connected": { tr: "CANLI", en: "LIVE" },
  "live.disconnected": { tr: "ÇEVRİMDIŞI", en: "OFFLINE" },

  // HotBadge
  "hot.label": { tr: "GÜNCEL", en: "HOT" },

  // Search
  "search.placeholder": { tr: "LLM haberlerinde ara…", en: "Search LLM news…" },
  "search.clear": { tr: "Aramayı temizle", en: "Clear search" },
  "search.searching": { tr: "Aranıyor…", en: "Searching…" },
  "search.noResults": {
    tr: "\"{query}\" için sonuç bulunamadı",
    en: "No results for \"{query}\"",
  },
  "search.resultCount": {
    tr: "{count} sonuç",
    en: "{count} result{plural}",
  },

  // FeedList
  "feed.empty.title": { tr: "Haber bulunamadı", en: "No articles found" },
  "feed.empty.subtitle": {
    tr: "Filtrelerinizi değiştirmeyi deneyin veya daha sonra kontrol edin",
    en: "Try adjusting your filters or check back later",
  },
  "feed.loadMore": { tr: "Daha fazla yükle", en: "Load more" },
  "feed.loading": { tr: "Yükleniyor…", en: "Loading…" },

  // FeedCard
  "card.importance": { tr: "{score}/10", en: "{score}/10" },
  "card.related": { tr: "İlişkili haberler", en: "Related articles" },
  "card.openOriginal": { tr: "Kaynağı aç", en: "Open original" },

  // SummaryToggle
  "summary.tr": { tr: "TR", en: "TR" },
  "summary.en": { tr: "EN", en: "EN" },

  // RelatedDrawer
  "related.title": { tr: "İlişkili Haberler", en: "Related Articles" },
  "related.close": { tr: "Çekmeceyi kapat", en: "Close drawer" },
  "related.loading": {
    tr: "İlişkili haberler aranıyor…",
    en: "Finding related articles…",
  },
  "related.empty": {
    tr: "İlişkili haber bulunamadı",
    en: "No related articles found",
  },
  "related.similarity": { tr: "%{pct} benzerlik", en: "{pct}% match" },

  // Error page
  "error.title": { tr: "Bir sorun oluştu", en: "Something went wrong" },
  "error.description": {
    tr: "Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.",
    en: "An unexpected error occurred. Please try again.",
  },
  "error.retry": { tr: "Tekrar dene", en: "Try again" },

  // Language toggle
  "lang.switch": { tr: "EN", en: "TR" },
  "lang.label": { tr: "Switch to English", en: "Türkçe'ye geç" },
} as const;

export type TranslationKey = keyof typeof translations;

export function t(
  key: TranslationKey,
  locale: Locale,
  vars?: Record<string, string | number>,
): string {
  const entry = translations[key];
  let text: string = entry[locale];

  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      text = text.replaceAll(`{${k}}`, String(v));
    }
  }

  return text;
}
