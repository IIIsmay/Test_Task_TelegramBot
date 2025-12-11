import json
import logging
import requests

from app.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

SYSTEM_PROMPT = """
Ты ассистент, который переводит русскоязычный запрос пользователя
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
  "query_type": 
    "count_videos" 
    | "sum_delta_metric" 
    | "count_distinct_videos_delta_gt_zero" 
    | "sum_final_metric"
    | "count_negative_deltas"
    | "sum_delta_metric_interval",

  "metric": "views" | "likes" | "comments" | "reports" | null,

  "filters": {
    "creator_id": string | null,
    "video_created_at_from": "YYYY-MM-DD" | null,
    "video_created_at_to": "YYYY-MM-DD" | null,
    "snapshot_date": "YYYY-MM-DD" | null,
    "snapshot_time_from": "HH:MM" | null,
    "snapshot_time_to": "HH:MM" | null,
    "final_views_gt": number | null
  }
}

Правила:

1) "Сколько всего видео"
→ query_type="count_videos"

2) "Сколько видео у креатора X"
→ count_videos + creator_id

3) "Сколько видео у креатора X с даты A по дату B"
→ count_videos + creator_id + date_from + date_to

4) "Сколько видео набрало больше N просмотров"
→ count_videos + final_views_gt

5) "Сколько видео у креатора X набрали больше N просмотров"
→ count_videos + creator_id + final_views_gt

6) "На сколько просмотров выросли все видео ДАТА"
→ sum_delta_metric + metric="views" + snapshot_date

7) "Сколько разных видео получали новые просмотры ДАТА"
→ count_distinct_videos_delta_gt_zero + metric="views" + snapshot_date

8) "Какое суммарное количество просмотров набрали видео"
→ query_type="sum_final_metric" + metric="views"

9) "Сколько всего лайков / комментариев / репортов у всех видео"
→ sum_final_metric + metric=<likes/comments/reports>

10) Периоды ("в июне 2025", "в 2025", "с 1 по 10 ноября")
→ добавляй video_created_at_from и video_created_at_to

11) "Сколько замеров, где просмотры уменьшились" / "отрицательные просмотры"
→ query_type="count_negative_deltas" + metric="views"

12) "На сколько просмотров выросли в промежутке с 10:00 до 15:00 ДАТА"
→ query_type="sum_delta_metric_interval"
→ metric="views"
→ snapshot_date + snapshot_time_from + snapshot_time_to

Ответ: только JSON, без текста, без комментариев.
"""



def call_llm(messages):
    if settings.ai_provider != "openrouter":
        raise RuntimeError("AI_PROVIDER должен быть openrouter")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "https://github.com/doxi-ai/video-analytics-bot",
        "X-Title": "video-analytics-bot"
    }

    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": 0
    }

    logger.info("Calling OpenRouter model=%s", settings.openrouter_model)

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        logger.error("OpenRouter error %s: %s", response.status_code, response.text)
        response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()

    logger.info("LLM raw output: %s", content)

    return content


async def parse_query(text: str):
    logger.info("Parsing user query: %s", text)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]

    llm_output = call_llm(messages)

    try:
        parsed = json.loads(llm_output)
        logger.info("Parsed JSON: %s", parsed)
        return parsed
    except Exception as e:
        logger.error("Failed to parse JSON: %s", e)
        raise RuntimeError("LLM вернул невалидный JSON")
