# Test_Task_TelegramBot
Бот, который отвечает на текстовые запросы о видео-статистике (просмотры, лайки и пр.), преобразуя их в SQL-запросы и выполняя обращения к базе данных. В качестве движка обработки естественного языка используется LLM (OpenRouter).

Настройка Telegram токена:
1. Перейдите в @BotFather
2. Создайте бота командой /newbot
3. Получите BOT_TOKEN
4. Вставьте его в .env
6. BOT_TOKEN=ваш_токен_от_BotFather

.Создайте .env файл в корне:
BOT_TOKEN=ваш_telegram_token
DATABASE_URL=postgresql://user:password@db:5432/video_db
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=ваш_openrouter_ключ
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct


Затем запустите:
docker compose up --build

Архитектура и логика
├── app/
│   ├── bot.py            # Телеграм-бот и обработка команд
│   ├── main.py           # Точка входа
│   ├── db.py             # Работа с PostgreSQL
│   ├── config.py         # Загрузка конфигурации из .env
│   ├── nlp.py            # NLP + LLM + генерация SQL
│   ├── query_builder.py  # Построение SQL-запросов
│   ├── apply_migrations.py # SQL-инициализация
│   ├── load_json.py      # Загрузка JSON-данных
│   └── logging.conf      # Конфиг логгера
├── data/
│   └── videos.json       # Исходные данные
├── migrations.sql        # SQL-структура таблиц
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md


Промпт:
"""
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
