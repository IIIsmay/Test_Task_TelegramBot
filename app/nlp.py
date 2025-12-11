import json
import logging
from typing import Any, Dict

import requests

from app.config import Settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Ты ассистент, который переводит русскоязычные запросы пользователя
в СТРОГО ВАЛИДНЫЙ JSON без пояснений и без текста вокруг.

Есть база данных PostgreSQL с таблицами:

videos:
- id (UUID)
- creator_id (UUID)
- video_created_at (timestamptz)
- views_count
- likes_count
- comments_count
- reports_count

video_snapshots:
- id (UUID)
- video_id (UUID)
- delta_views_count
- delta_likes_count
- delta_comments_count
- delta_reports_count
- created_at (timestamptz)

Верни JSON строго такого формата:

{
  "query_type": "count_videos" | "sum_delta_metric" | "count_distinct_videos_delta_gt_zero",
  "metric": "views" | "likes" | "comments" | "reports" | null,
  "filters": {
    "creator_id": string | null,
    "video_created_at_from": "YYYY-MM-DD" | null,
    "video_created_at_to": "YYYY-MM-DD" | null,
    "snapshot_date": "YYYY-MM-DD" | null,
    "final_views_gt": number | null
  }
}

Правила:
- "Сколько всего видео" → count_videos
- "Сколько видео у креатора X с даты A по B" → count_videos + creator_id + даты
- "Сколько видео набрало больше N просмотров" → count_videos + final_views_gt
- "На сколько просмотров выросли все видео ДАТА" → sum_delta_metric + metric=views
- "Сколько разных видео получали новые просмотры ДАТА"
  → count_distinct_videos_delta_gt_zero + metric=views

Ответ:
- ТОЛЬКО JSON
- без комментариев
- без текста
"""

def get_settings() -> Settings:
    return Settings()


def call_llm(messages) -> Dict[str, Any]:
    settings = get_settings()

    if settings.ai_provider != "openrouter":
        raise RuntimeError("AI_PROVIDER должен быть openrouter")

    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY не задан")

    logger.info("Calling OpenRouter model=%s", settings.openrouter_model)

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "telegram-video-analytics-bot",
        },
        json={
            "model": settings.openrouter_model,
            "messages": messages,
            "temperature": 0,
        },
        timeout=30,
    )

    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    logger.info("LLM raw response: %s", content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON from LLM:\n{content}")


async def parse_query(user_text: str) -> Dict[str, Any]:
    logger.info("Parsing user query: %s", user_text)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    return call_llm(messages)
