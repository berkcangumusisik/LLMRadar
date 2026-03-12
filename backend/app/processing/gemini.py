from __future__ import annotations

import asyncio
import json
import logging
import re
import time

import google.generativeai as genai

from app.core.config import get_settings
from app.models.schemas import GeminiAnalysis

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Sen bir yapay zeka haberleri analiz uzmanısın.\n"
    "SADECE geçerli JSON döndür. Başka hiçbir şey yazma."
)

USER_TEMPLATE = """Aşağıdaki haberi analiz et ve tam olarak bu JSON formatında döndür:

{{
  "category_tags": [],
  "model_tags": [],
  "summary_en": "",
  "summary_tr": "",
  "importance": 0,
  "is_llm_related": true,
  "key_metric": ""
}}

KATEGORİ ETİKETLERİ (max 2, sadece listeden seç):
Model Release, Benchmark, Research, Safety & Alignment,
API & Pricing, Company News, Open Source, Multimodal,
Fine-tuning, Agentic AI, Regulation

MODEL ETİKETLERİ (max 3, sadece listeden seç):
GPT, Claude, Gemini, Llama, Mistral, DeepSeek,
Grok, Qwen, Command R, Phi, Sora, DALL-E

ÖNEM SKORU:
10  = GPT-5, Claude 5 gibi devasa model çıkışı
8-9 = Önemli benchmark, büyük şirket haberi
6-7 = Yeni araç, orta ölçekli model çıkışı
4-5 = Araştırma makalesi, küçük güncelleme
1-3 = Yorum, tartışma, görüş yazısı

KURALLAR:
- summary_en ve summary_tr tam 2 cümle olsun
- Rakam varsa mutlaka ekle (%23 daha hızlı gibi)
- is_llm_related false ise kaydet ama öne çıkarma
- key_metric: en çarpıcı tek rakam/metrik, yoksa boş string

KAYNAK: {source}
BAŞLIK: {title}
İÇERİK: {content}"""

_model: genai.GenerativeModel | None = None

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Model Release": ["release", "launch", "announce", "introducing", "new model", "available", "çıktı", "yayınlandı"],
    "Benchmark": ["benchmark", "eval", "score", "leaderboard", "mmlu", "humaneval", "sota", "state-of-the-art"],
    "Research": ["paper", "arxiv", "research", "study", "propose", "method", "novel", "approach", "araştırma"],
    "Safety & Alignment": ["safety", "alignment", "rlhf", "red team", "guardrail", "toxic", "bias", "harm"],
    "API & Pricing": ["api", "pricing", "token", "rate limit", "endpoint", "cost", "free tier", "quota"],
    "Company News": ["funding", "acquisition", "hire", "ceo", "partnership", "valuation", "billion"],
    "Open Source": ["open source", "open-source", "github", "apache", "mit license", "weights", "huggingface"],
    "Multimodal": ["multimodal", "vision", "image", "video", "audio", "speech", "visual"],
    "Fine-tuning": ["fine-tun", "lora", "qlora", "adapter", "peft", "instruction tuning", "sft"],
    "Agentic AI": ["agent", "agentic", "tool use", "function call", "autonomous", "planning", "reasoning"],
    "Regulation": ["regulation", "eu ai act", "executive order", "policy", "legislation", "compliance", "govern"],
}

MODEL_KEYWORDS: dict[str, list[str]] = {
    "GPT": ["gpt-4", "gpt-5", "gpt4", "gpt5", "openai", "chatgpt"],
    "Claude": ["claude", "anthropic"],
    "Gemini": ["gemini", "google ai", "deepmind", "bard"],
    "Llama": ["llama", "meta ai"],
    "Mistral": ["mistral", "mixtral"],
    "DeepSeek": ["deepseek"],
    "Grok": ["grok", "xai"],
    "Qwen": ["qwen", "alibaba"],
    "Command R": ["command r", "cohere"],
    "Phi": ["phi-", "phi3", "phi4", "microsoft phi"],
    "Sora": ["sora"],
    "DALL-E": ["dall-e", "dalle"],
}

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


class _CircuitBreaker:
    """Prevents hammering Gemini when quota is exhausted."""

    def __init__(self, cooldown: float = 300.0):
        self._cooldown = cooldown
        self._open_until: float = 0.0
        self._consecutive_failures: int = 0

    @property
    def is_open(self) -> bool:
        return time.monotonic() < self._open_until

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._open_until = 0.0

    def record_failure(self, is_quota_error: bool = False) -> None:
        self._consecutive_failures += 1
        if is_quota_error or self._consecutive_failures >= 5:
            self._open_until = time.monotonic() + self._cooldown
            logger.warning(
                "Circuit breaker OPEN — skipping Gemini for %.0fs (failures: %d)",
                self._cooldown,
                self._consecutive_failures,
            )


_breaker = _CircuitBreaker(cooldown=300.0)


def _get_model() -> genai.GenerativeModel:
    global _model
    if _model is None:
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=8192,
                response_mime_type="application/json",
            ),
        )
    return _model


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def _extract_sentences(text: str, count: int = 3) -> str:
    """Extract first N meaningful sentences from raw text."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    sentences = _SENTENCE_RE.split(cleaned)
    meaningful = [s.strip() for s in sentences if len(s.strip()) > 30]
    return " ".join(meaningful[:count]) if meaningful else cleaned[:400]


def _detect_tags(title: str, content: str) -> tuple[list[str], list[str]]:
    """Keyword-based category and model tag detection."""
    combined = f"{title} {content}".lower()

    cats: list[str] = []
    for tag, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            cats.append(tag)
        if len(cats) >= 2:
            break

    models: list[str] = []
    for tag, keywords in MODEL_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            models.append(tag)
        if len(models) >= 3:
            break

    return cats, models


def _extract_numbers(text: str) -> list[str]:
    """Pull key numbers/metrics from text."""
    patterns = [
        r"\d+\.?\d*[%x×]",
        r"\d+\.?\d*\s*(?:billion|million|trillion|B|M|T)\b",
        r"\d+\.?\d*\s*(?:tokens?/s|tok/s|fps|MMLU|params?)\b",
    ]
    hits: list[str] = []
    for pat in patterns:
        hits.extend(re.findall(pat, text, re.IGNORECASE))
    return hits[:3]


_SOURCE_TR: dict[str, str] = {
    "arxiv": "arXiv",
    "hackernews": "Hacker News",
    "huggingface": "Hugging Face",
    "paperswithcode": "Papers With Code",
    "devto": "Dev.to",
    "github_trending": "GitHub",
    "semanticscholar": "Semantic Scholar",
}

_CAT_TR: dict[str, str] = {
    "Model Release": "yeni model duyurusu",
    "Benchmark": "benchmark/performans karşılaştırması",
    "Research": "araştırma makalesi",
    "Safety & Alignment": "güvenlik ve hizalama",
    "API & Pricing": "API ve fiyatlandırma",
    "Company News": "şirket haberi",
    "Open Source": "açık kaynak",
    "Multimodal": "çoklu modalite (görüntü/ses/metin)",
    "Fine-tuning": "ince ayar (fine-tuning)",
    "Agentic AI": "otonom AI ajanları",
    "Regulation": "düzenleme ve mevzuat",
}


def _build_fallback(title: str, content: str, source: str) -> GeminiAnalysis:
    """Build a rich fallback analysis from article content itself."""
    core_sentences = _extract_sentences(content, count=2)

    if len(core_sentences) < 40:
        core_sentences = _extract_sentences(f"{title}. {content}", count=2)

    numbers = _extract_numbers(f"{title} {content}")
    key_metric = numbers[0] if numbers else ""

    cats, models = _detect_tags(title, content)

    model_mention = f" ({', '.join(models)})" if models else ""

    summary_en = f"{title.rstrip('.')}.{model_mention} {core_sentences}"
    if len(summary_en) > 500:
        summary_en = summary_en[:497] + "..."

    source_base = source.split("_", 1)[0] if source.startswith("blog_") else source
    source_tr = _SOURCE_TR.get(source_base, source)
    if source.startswith("blog_"):
        source_tr = source.replace("blog_", "").replace("_", " ").title() + " Blog"
    if source.startswith("reddit_"):
        source_tr = f"Reddit r/{source.replace('reddit_', '')}"

    cat_tr = _CAT_TR.get(cats[0], "yapay zeka") if cats else "yapay zeka"
    model_tr = f" {', '.join(models)} ile ilgili" if models else ""

    metric_tr = ""
    if key_metric:
        metric_tr = f" (Öne çıkan metrik: {key_metric})"

    summary_tr = (
        f"{source_tr} kaynağından{model_tr} {cat_tr} haberi: "
        f"{title}.{metric_tr} {core_sentences}"
    )
    if len(summary_tr) > 500:
        summary_tr = summary_tr[:497] + "..."

    return GeminiAnalysis(
        category_tags=cats,
        model_tags=models,
        summary_en=summary_en,
        summary_tr=summary_tr,
        importance=5,
        is_llm_related=True,
        key_metric=key_metric,
    )


async def analyze_article(
    title: str,
    content: str,
    source: str,
) -> tuple[GeminiAnalysis, bool]:
    """Returns (analysis, used_fallback)."""
    settings = get_settings()

    if _breaker.is_open:
        logger.debug("Circuit breaker open — using fallback for: %s", title[:60])
        return _build_fallback(title, content, source), True

    model = _get_model()

    prompt = USER_TEMPLATE.format(
        source=source,
        title=title,
        content=content[:4000],
    )

    try:
        response = await asyncio.to_thread(
            model.generate_content, prompt
        )
        raw = _extract_json(response.text)
        analysis = GeminiAnalysis(**raw)
        _breaker.record_success()
        await asyncio.sleep(settings.GEMINI_RATE_LIMIT_DELAY)
        return analysis, False
    except Exception as exc:
        is_quota = "429" in str(exc) or "ResourceExhausted" in type(exc).__name__
        _breaker.record_failure(is_quota_error=is_quota)
        logger.warning("Gemini failed for: %s (%s)", title[:60], type(exc).__name__)
        return _build_fallback(title, content, source), True
