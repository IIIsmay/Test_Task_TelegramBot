import psycopg2

conn = psycopg2.connect(
    "postgresql://postgres:12345@localhost:5432/video_db"
)
print("PostgreSQL доступен")
conn.close()
