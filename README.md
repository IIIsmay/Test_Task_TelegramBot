# Test_Task_TelegramBot
Бот, который отвечает на текстовые запросы о видео-статистике (просмотры, лайки и пр.), преобразуя их в SQL-запросы и выполняя обращения к базе данных. В качестве движка обработки естественного языка используется LLM (OpenRouter).

## Настройка Telegram токена:
1. Перейдите в @BotFather
2. Создайте бота командой /newbot
3. Получите BOT_TOKEN
4. Вставьте его в .env
6. BOT_TOKEN=ваш_токен_от_BotFather

## Создайте .env файл в корне:
- BOT_TOKEN=ваш_telegram_token
- DATABASE_URL=postgresql://user:password@db:5432/video_db
- AI_PROVIDER=openrouter
- OPENROUTER_API_KEY=ваш_openrouter_ключ
- OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct


## Затем запустите:
docker compose up --build

## Архитектура и логика
- ── app/
- ── bot.py # Телеграм-бот и обработка команд
- ├── main.py # Точка входа приложения
- ├── db.py # Работа с PostgreSQL
- ├── config.py # Загрузка конфигурации из .env
- ├── nlp.py # Вызов LLM и извлечение структуры запроса
- ├── query_builder.py # Преобразование структуры в SQL
- ├── apply_migrations.py # Применение SQL-моделей
- ├── load_json.py # Загрузка JSON данных
- └── logger.py # Логирование
- ── data/
- └── videos.json # Исходные данные
- ── migrations.sql # SQL-схема таблиц
- ── requirements.txt
- ── Dockerfile
- ── docker-compose.yml
- ── README.md
- ──.env


## Промпт:
"""
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

Возвращай JSON строго такого формата:

{
  "query_type":
      "count_videos" |
      "sum_delta_metric" |
      "count_distinct_videos_delta_gt_zero" |
      "sum_final_metric" |
      "sum_delta_metric_interval" |
      "count_negative_deltas" |
      "count_creators_with_video_condition",

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

3) "Сколько видео в периоде / с даты A по B / в июне"
   → count_videos + date_from + date_to

4) "Сколько видео набрало больше N просмотров"
   → count_videos + final_views_gt

5) "Сколько видео у креатора X набрали больше N"
   → count_videos + creator_id + final_views_gt

6) "На сколько просмотров выросли все видео ДАТА"
   → sum_delta_metric + metric="views" + snapshot_date

7) "Сколько разных видео получали новые просмотры ДАТА"
   → count_distinct_videos_delta_gt_zero + metric="views" + snapshot_date

8) "Сколько всего просмотров/лайков/комментариев/репортов у всех видео"
   → sum_final_metric + metric

9) "Сколько просмотров/лайков и т.п. набрали видео за период"
   → sum_final_metric + metric + date_from/to

10) "В промежутке с 10:00 до 15:00"
    → snapshot_time_from / snapshot_time_to

11) "Сколько суммарно выросли просмотры в интервале времени"
    → query_type="sum_delta_metric_interval" + metric="views"

12) "Когда просмотры уменьшились / были отрицательные дельты"
    → query_type="count_negative_deltas" + metric=<views/likes/comments/reports>

13) "Сколько разных креаторов имеют хотя бы одно видео с условием"
    например "больше 100 000 просмотров"
    → query_type="count_creators_with_video_condition" + final_views_gt=N

Ответ — строго JSON без текста.
"""
