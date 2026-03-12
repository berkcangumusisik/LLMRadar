from __future__ import annotations

import asyncio
import json
import logging

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


def _get_model() -> genai.GenerativeModel:
    global _model
    if _model is None:
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024,
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
    return json.loads(text)


async def analyze_article(
    title: str,
    content: str,
    source: str,
) -> GeminiAnalysis:
    settings = get_settings()
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
    except Exception:
        logger.exception("Gemini analysis failed for: %s", title[:80])
        analysis = GeminiAnalysis(
            summary_en=f"AI news from {source}: {title[:100]}",
            summary_tr=f"{source} kaynağından AI haberi: {title[:100]}",
        )

    await asyncio.sleep(settings.GEMINI_RATE_LIMIT_DELAY)
    return analysis
