# LLMRadar

> A real-time, AI-powered news aggregation platform for tracking large language model developments.

[Türkçe dokümantasyon →](./README.md)

---

## What is it?

LLMRadar automatically collects news about large language models — GPT, Claude, Gemini, Llama, DeepSeek and more — from **5 different sources**, analyzes and tags them using **Google Gemini Flash**, generates bilingual (TR/EN) summaries, streams updates in real-time via **WebSocket**, and finds related articles using **pgvector** cosine similarity search.

## Key Features

- **Multi-Source Ingestion** — arXiv, Hacker News, Hugging Face, official AI blogs (OpenAI, Anthropic, Google, Meta), and X (Twitter) accounts
- **Smart Tagging** — Gemini Flash assigns category tags, model tags, importance scores (1-10), and key metrics
- **Bilingual Summaries** — 2-sentence Turkish and English summaries for every article
- **Real-Time Streaming** — Instant push notifications via Supabase Realtime + WebSocket
- **Semantic Search** — pgvector cosine similarity for related article discovery
- **Bilingual UI** — Full Turkish/English interface with one-click toggle
- **Atomic Design** — Atoms → Molecules → Organisms → Templates architecture

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python 3.10+ | Core language |
| FastAPI | REST API + WebSocket server |
| SQLAlchemy 2.0 (async) | ORM with asyncpg driver |
| APScheduler | Scheduled news ingestion |
| supabase-py | Supabase client + Realtime listener |
| google-generativeai | Gemini Flash for article analysis |
| sentence-transformers | all-MiniLM-L6-v2 for 384-dim embeddings |

### Frontend
| Technology | Purpose |
|---|---|
| Next.js 16 | App Router + Turbopack |
| TypeScript | Type safety |
| Tailwind CSS v4 | Styling |
| @supabase/supabase-js | Supabase client |
| Recharts | Charts |
| Lucide React | Icons |

### Infrastructure
| Service | Purpose |
|---|---|
| Supabase | PostgreSQL + pgvector + Realtime |
| Vercel | Frontend deployment |
| Render | Backend deployment |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Sources   │────▶│   Backend    │────▶│  Supabase   │
│ arXiv, HN,  │     │  FastAPI     │     │ PostgreSQL  │
│ HF, Blogs,  │     │  + Gemini    │     │ + pgvector  │
│ X (RSSHub)  │     │  + Embedder  │     │ + Realtime  │
└─────────────┘     └──────┬───────┘     └──────┬──────┘
                           │                     │
                    WebSocket push        Realtime INSERT
                           │                     │
                    ┌──────▼───────┐     ┌───────▼──────┐
                    │  Frontend    │◀────│  Supabase    │
                    │  Next.js 16  │     │  Realtime    │
                    └──────────────┘     └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Supabase account
- Google AI Studio API key

### 1. Supabase Setup

Create a new project at [supabase.com](https://supabase.com) and run the following in the SQL Editor:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Articles table
CREATE TABLE articles (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title           text NOT NULL,
  content         text NOT NULL,
  url             text UNIQUE NOT NULL,
  source          text NOT NULL,
  author          text,
  category_tags   text[] NOT NULL DEFAULT '{}',
  model_tags      text[] NOT NULL DEFAULT '{}',
  summary_en      text,
  summary_tr      text,
  importance      integer NOT NULL DEFAULT 5,
  key_metric      text,
  is_llm_related  boolean NOT NULL DEFAULT true,
  embedding       vector(384),
  published_at    timestamptz NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_articles_published_at ON articles (published_at DESC);
CREATE INDEX idx_articles_importance ON articles (importance DESC);
CREATE INDEX idx_articles_source ON articles (source);
CREATE INDEX idx_articles_embedding ON articles
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Enable Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE articles;

-- Similarity search function
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

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Configure your environment (use `backend/.env.example` as reference):

```bash
cp .env.example .env
# Edit: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL, GEMINI_API_KEY
```

Start the server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Configure your environment (use `frontend/.env.example` as reference):

```bash
cp .env.example .env.local
# Edit: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
```

Start the dev server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
llmradar/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, DB connection, Supabase client
│   │   ├── models/         # SQLAlchemy model + Pydantic schemas
│   │   ├── ingestion/      # News sources, dedup, pipeline, scheduler
│   │   ├── processing/     # Gemini analysis + embedding generation
│   │   ├── rag/            # pgvector related article search
│   │   ├── realtime/       # WebSocket manager + Supabase Realtime listener
│   │   ├── api/            # REST endpoints + WebSocket endpoint
│   │   └── main.py         # FastAPI app + lifespan
│   ├── .env.example
│   └── requirements.txt
│
└── frontend/
    ├── app/                # Next.js App Router (layout, page, loading, error)
    ├── components/
    │   ├── atoms/          # TagBadge, LiveBadge, HotBadge, SkeletonLine, etc.
    │   ├── molecules/      # CardHeader, TagGroup, SummaryToggle, SearchInput, etc.
    │   ├── organisms/      # FeedCard, FeedList, SearchBar, RelatedDrawer, etc.
    │   └── templates/      # FeedTemplate
    ├── hooks/              # useWebSocket, useFeed, useSearch, useLanguage
    ├── lib/                # types, constants, utils, i18n, supabase client
    └── .env.example
```

## News Sources & Intervals

| Source | Interval | Description |
|---|---|---|
| arXiv | 60 min | cs.AI, cs.CL, cs.LG categories |
| Hacker News | 15 min | LLM keyword-filtered recent stories |
| Hugging Face | 30 min | Daily papers + trending repos |
| Official Blogs | 30 min | OpenAI, Anthropic, Google AI, Meta AI |
| X (RSSHub) | 20 min | 18 AI leader/organization accounts |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/feed` | Paginated news feed (filterable) |
| GET | `/api/articles/{id}` | Single article detail |
| GET | `/api/articles/{id}/related` | Related articles (pgvector) |
| GET | `/api/sources` | Source statistics |
| GET | `/api/stats` | General statistics |
| WS | `/ws` | Live news stream + search |
| GET | `/health` | Health check |

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (full access) |
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google AI Studio API key |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anonymous (public) key |
| `NEXT_PUBLIC_WS_URL` | Backend WebSocket URL |
| `NEXT_PUBLIC_API_URL` | Backend REST API URL |

## License

MIT
