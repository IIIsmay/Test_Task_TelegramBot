import json
import logging
import requests

from app.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

SYSTEM_PROMPT = """
Ты ассистент, который переводит русскоязычный запрос пользователя в СТРОГО ВАЛИДНЫЙ JSON 
без пояснений и без текста вокруг.

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
  "query_type": "count_videos" 
                | "sum_delta_metric" 
                | "count_distinct_videos_delta_gt_zero"
                | "sum_final_metric"
                | "sum_delta_metric_interval"
                | "count_negative_deltas",
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

Пояснения для выбора query_type:

1) "Сколько всего видео"
→ query_type = "count_videos"

2) "Сколько видео у креатора X"
→ count_videos + creator_id

3) Любые фразы о периодах ("в июне", "в 2025", "с 1 по 10 ноября")
→ используй video_created_at_from и video_created_at_to

4) "Сколько видео набрали больше N просмотров"
→ count_videos + final_views_gt

5) "Сколько видео у креатора X набрали больше N просмотров"
→ count_videos + creator_id + final_views_gt

6) "На сколько просмотров выросли все видео ДАТА"
→ sum_delta_metric + metric="views" + snapshot_date

7) "Сколько разных видео получали новые просмотры ДАТА"
→ count_distinct_videos_delta_gt_zero + metric="views" + snapshot_date

8) "Какое суммарное количество просмотров набрали видео"
→ sum_final_metric + metric="views"

9) "Сколько всего лайков / комментариев / репортов у всех видео"
→ sum_final_metric + metric=<likes/comments/reports>

10) Интервалы по времени:
   Если запрос содержит "между 10 и 15", "с 01:00 по 03:00", "за час", 
   используй snapshot_time_from и snapshot_time_to.

   → Если просится суммировать изменения: query_type="sum_delta_metric_interval"

11) Если упоминается, что просмотры стали меньше, уменьшились, отрицательные изменения:
   → query_type="count_negative_deltas"
   metric="views"

Правила:
- Всегда возвращай один JSON-объект.
- Никаких комментариев, никакого текста вокруг JSON.
- Значения timestamp-ов по времени только в формате HH:MM.
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
