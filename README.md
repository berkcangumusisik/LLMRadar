# LLMRadar

> Büyük dil modelleri hakkındaki haberleri gerçek zamanlı takip eden, yapay zeka destekli haber akışı platformu.

[English documentation →](./README.en.md)

---

## Nedir?

LLMRadar, GPT, Claude, Gemini, Llama, DeepSeek gibi büyük dil modelleri hakkındaki haberleri **9 farklı kaynaktan** otomatik olarak çeken, **Google Gemini 2.5 Flash** ile analiz edip etiketleyen, Türkçe ve İngilizce özetleyen, **WebSocket** ile canlı yayınlayan ve **pgvector** ile ilişkili haberleri bulan bir platformdur.

## Öne Çıkan Özellikler

- **Çoklu Kaynak Toplama** — arXiv, Hacker News, Hugging Face, Google AI Blog, Reddit, Papers With Code, Dev.to, GitHub Trending, Semantic Scholar, TechCrunch, The Verge, VentureBeat, Ars Technica
- **Akıllı Etiketleme** — Gemini 2.5 Flash ile kategori etiketleri, model etiketleri, önem skoru (1-10) ve anahtar metrik çıkarımı
- **İki Dilli Özet** — Her haber için 2 cümlelik Türkçe ve İngilizce özet
- **Gerçek Zamanlı Akış** — Supabase Realtime + WebSocket ile anında haber bildirimi
- **Semantik Arama** — pgvector ile cosine similarity tabanlı ilişkili haber bulma
- **İki Dilli Arayüz** — Tüm UI Türkçe/İngilizce, tek tıkla geçiş
- **Atomic Design** — Atoms → Molecules → Organisms → Templates mimarisi
- **Circuit Breaker** — Gemini API kotası dolduğunda akıllı fallback + otomatik retry
- **Akıllı Fallback** — Gemini ulaşılamazsa bile keyword-based etiketleme, metrik çıkarımı ve içerikten özet üretimi
- **Tarih Filtresi** — Geçmiş haberler yerine sadece güncel haberler çekilir

## Teknik Yığın

### Backend
| Teknoloji | Kullanım |
|---|---|
| Python 3.10+ | Ana dil |
| FastAPI | REST API + WebSocket sunucu |
| SQLAlchemy 2.0 (async) | ORM — asyncpg driver |
| APScheduler | Zamanlanmış haber çekme |
| supabase-py | Supabase client + Realtime dinleme |
| google-generativeai | Gemini 2.5 Flash ile haber analizi |
| sentence-transformers | all-MiniLM-L6-v2 ile 384-dim embedding |

### Frontend
| Teknoloji | Kullanım |
|---|---|
| Next.js 16 | App Router + Turbopack |
| TypeScript | Tip güvenliği |
| Tailwind CSS v4 | Stil |
| @supabase/supabase-js | Supabase client |
| Recharts | Grafikler |
| Lucide React | İkonlar |

### Altyapı
| Hizmet | Kullanım |
|---|---|
| Supabase | PostgreSQL + pgvector + Realtime |
| Vercel | Frontend deploy |
| Render | Backend deploy |

## Mimari

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Kaynaklar  │────▶│   Backend    │────▶│  Supabase   │
│ arXiv, HN,  │     │  FastAPI     │     │ PostgreSQL  │
│ HF, Reddit, │     │  + Gemini    │     │ + pgvector  │
│ PwC, DevTo, │     │  + Embedder  │     │ + Realtime  │
│ GitHub, SS, │     │  + Circuit   │     │             │
│ Blogs (5)   │     │    Breaker   │     │             │
└─────────────┘     └──────┬───────┘     └──────┬──────┘
                           │                     │
                    WebSocket push        Realtime INSERT
                           │                     │
                    ┌──────▼───────┐     ┌───────▼──────┐
                    │  Frontend    │◀────│  Supabase    │
                    │  Next.js 16  │     │  Realtime    │
                    └──────────────┘     └──────────────┘
```

## Hızlı Başlangıç

### Gereksinimler

- Python 3.10+
- Node.js 18+
- Supabase hesabı
- Google AI Studio API anahtarı

### 1. Supabase Kurulumu

[supabase.com](https://supabase.com)'da yeni proje oluşturun ve SQL Editor'da şu komutları çalıştırın:

```sql
-- pgvector uzantısını etkinleştir
CREATE EXTENSION IF NOT EXISTS vector;

-- articles tablosu
CREATE TABLE articles (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title             text NOT NULL,
  content           text NOT NULL,
  url               text UNIQUE NOT NULL,
  source            text NOT NULL,
  author            text,
  category_tags     text[] NOT NULL DEFAULT '{}',
  model_tags        text[] NOT NULL DEFAULT '{}',
  summary_en        text,
  summary_tr        text,
  importance        integer NOT NULL DEFAULT 5,
  key_metric        text,
  is_llm_related    boolean NOT NULL DEFAULT true,
  needs_reanalysis  boolean NOT NULL DEFAULT false,
  embedding         vector(384),
  published_at      timestamptz NOT NULL,
  created_at        timestamptz NOT NULL DEFAULT now()
);

-- İndeksler
CREATE INDEX idx_articles_published_at ON articles (published_at DESC);
CREATE INDEX idx_articles_importance ON articles (importance DESC);
CREATE INDEX idx_articles_source ON articles (source);
CREATE INDEX idx_articles_embedding ON articles
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Realtime'ı etkinleştir
ALTER PUBLICATION supabase_realtime ADD TABLE articles;

-- Benzerlik arama fonksiyonu
CREATE OR REPLACE FUNCTION match_articles(
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  exclude_id uuid
)
RETURNS TABLE (
  id uuid, title text, url text, source text,
  category_tags text[], model_tags text[],
  summary_tr text, summary_en text,
  importance int, published_at timestamptz,
  similarity float
)
LANGUAGE sql STABLE AS $$
  SELECT
    a.id, a.title, a.url, a.source,
    a.category_tags, a.model_tags,
    a.summary_tr, a.summary_en,
    a.importance, a.published_at,
    1 - (a.embedding <=> query_embedding) AS similarity
  FROM articles a
  WHERE
    a.id != exclude_id
    AND a.embedding IS NOT NULL
    AND 1 - (a.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
$$;
```

### 2. Backend Kurulumu

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

`.env` dosyasını doldurun (`backend/.env.example` referans alın):

```bash
cp .env.example .env
# Düzenleyin: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL, GEMINI_API_KEY
```

Sunucuyu başlatın:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Kurulumu

```bash
cd frontend
npm install
```

`.env.local` dosyasını doldurun (`frontend/.env.example` referans alın):

```bash
cp .env.example .env.local
# Düzenleyin: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
```

Geliştirme sunucusunu başlatın:

```bash
npm run dev
```

Tarayıcıda [http://localhost:3000](http://localhost:3000) adresini açın.

## Proje Yapısı

```
llmradar/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, DB bağlantısı, Supabase client
│   │   ├── models/         # SQLAlchemy modeli + Pydantic şemaları
│   │   ├── ingestion/      # Haber kaynakları, deduplikasyon, pipeline, scheduler
│   │   ├── processing/     # Gemini analizi + embedding üretimi
│   │   ├── rag/            # pgvector ile ilişkili haber bulma
│   │   ├── realtime/       # WebSocket manager + Supabase Realtime dinleyici
│   │   ├── api/            # REST endpoint'leri + WebSocket endpoint'i
│   │   └── main.py         # FastAPI uygulaması + lifespan
│   ├── .env.example
│   └── requirements.txt
│
└── frontend/
    ├── app/                # Next.js App Router (layout, page, loading, error)
    ├── components/
    │   ├── atoms/          # TagBadge, LiveBadge, HotBadge, SkeletonLine vb.
    │   ├── molecules/      # CardHeader, TagGroup, SummaryToggle, SearchInput vb.
    │   ├── organisms/      # FeedCard, FeedList, SearchBar, RelatedDrawer vb.
    │   └── templates/      # FeedTemplate
    ├── hooks/              # useWebSocket, useFeed, useSearch, useLanguage
    ├── lib/                # types, constants, utils, i18n, supabase client
    └── .env.example
```

## Haber Kaynakları & Çekme Sıklığı

| Kaynak | Aralık | Filtre | Açıklama |
|---|---|---|---|
| arXiv | 60 dk | Son 48 saat | cs.AI, cs.CL, cs.LG kategorileri |
| Hacker News | 15 dk | Son 24 saat | LLM keyword filtreli son haberler |
| Hugging Face | 30 dk | Son 48 saat | Daily papers + trending repos |
| Google AI Blog | 30 dk | Son 7 gün | Resmi Google AI blog RSS'i |
| Reddit | 20 dk | Son 24 saat | r/MachineLearning, r/LocalLLaMA, r/artificial |
| Papers With Code | 60 dk | Son 48 saat | En yeni ML makaleleri + kod linkleri |
| Dev.to | 30 dk | Son 48 saat | AI/ML/LLM etiketli yazılar |
| GitHub Trending | 60 dk | Günlük | AI/ML ile ilgili trend repolar |
| Semantic Scholar | 60 dk | Son 7 gün | Akademik LLM makaleleri |
| TechCrunch AI | 30 dk | Son 7 gün | AI sektör haberleri (RSS) |
| The Verge AI | 30 dk | Son 7 gün | Popüler AI haberleri (RSS) |
| VentureBeat AI | 30 dk | Son 7 gün | Enterprise AI haberleri (RSS) |
| Ars Technica | 30 dk | Son 7 gün | Teknik AI haberleri (RSS) |

## API Endpoint'leri

| Yöntem | Yol | Açıklama |
|---|---|---|
| GET | `/api/feed` | Sayfalanmış haber akışı (filtreli) |
| GET | `/api/articles/{id}` | Tekil haber detayı |
| GET | `/api/articles/{id}/related` | İlişkili haberler (pgvector) |
| GET | `/api/sources` | Kaynak bazlı istatistikler |
| GET | `/api/stats` | Genel istatistikler |
| WS | `/ws` | Canlı haber akışı + arama |
| GET | `/health` | Sağlık kontrolü |

## Ortam Değişkenleri

### Backend (`backend/.env`)
| Değişken | Açıklama |
|---|---|
| `SUPABASE_URL` | Supabase proje URL'i |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role anahtarı (tam yetki) |
| `DATABASE_URL` | PostgreSQL bağlantı dizesi (pooler önerilir) |
| `GEMINI_API_KEY` | Google AI Studio API anahtarı |

### Frontend (`frontend/.env.local`)
| Değişken | Açıklama |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase proje URL'i |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anonim (public) anahtar |
| `NEXT_PUBLIC_WS_URL` | Backend WebSocket URL'i |
| `NEXT_PUBLIC_API_URL` | Backend REST API URL'i |

## Lisans

MIT
