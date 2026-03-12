from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Supabase ---
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    DATABASE_URL: str

    # --- Gemini ---
    GEMINI_API_KEY: str

    # --- App ---
    APP_NAME: str = "LLMRadar"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://llmradar.vercel.app",
    ]

    # --- Scheduler intervals (minutes) ---
    ARXIV_INTERVAL: int = 60
    HACKERNEWS_INTERVAL: int = 15
    HUGGINGFACE_INTERVAL: int = 30
    BLOGS_INTERVAL: int = 30
    RSSHUB_INTERVAL: int = 20

    # --- Processing ---
    GEMINI_RATE_LIMIT_DELAY: float = 1.0
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SIMILARITY_THRESHOLD: float = 0.55
    RELATED_MATCH_COUNT: int = 5

    # --- WebSocket ---
    WS_PING_INTERVAL: int = 30

    # --- RSSHub ---
    RSSHUB_BASE_URL: str = "https://rsshub.app"
    NITTER_BASE_URL: str = "https://nitter.poast.org"

    X_ACCOUNTS: list[str] = [
        "openai",
        "anthropic",
        "GoogleDeepMind",
        "Meta_AI",
        "MistralAI",
        "xai",
        "huggingface",
        "sama",
        "karpathy",
        "ylecun",
        "demishassabis",
        "GaryMarcus",
        "ilyasut",
        "DrJimFan",
        "hardmaru",
        "TheRundownAI",
        "paperswithcode",
        "_akhaliq",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
