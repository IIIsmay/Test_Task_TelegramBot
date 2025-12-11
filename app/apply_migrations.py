import psycopg2
from app.config import Settings

settings = Settings()

with psycopg2.connect(settings.database_url) as conn:
    with conn.cursor() as cur:
        with open("app/migrations.sql", "r", encoding="utf-8") as f:
            cur.execute(f.read())

print("✅ Миграции применены")
