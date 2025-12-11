import json
import sys
from pathlib import Path
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_batch

from app.config import Settings


def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main(json_path: str):
    settings = Settings()
    conn = psycopg2.connect(settings.database_url)
    conn.autocommit = True

    with conn.cursor() as cur:
        path = Path(json_path)
        raw = json.loads(path.read_text(encoding="utf-8"))

        videos = raw["videos"]  # ✅ ключевой момент

        videos_rows = []
        snapshots_rows = []

        for v in videos:
            videos_rows.append((
                v["id"],
                v["creator_id"],
                parse_dt(v["video_created_at"]),
                v["views_count"],
                v["likes_count"],
                v["comments_count"],
                v["reports_count"],
                parse_dt(v["created_at"]),
                parse_dt(v["updated_at"]),
            ))

            for s in v.get("snapshots", []):
                snapshots_rows.append((
                    s["id"],
                    s["video_id"],
                    s["views_count"],
                    s["likes_count"],
                    s["comments_count"],
                    s["reports_count"],
                    s["delta_views_count"],
                    s["delta_likes_count"],
                    s["delta_comments_count"],
                    s["delta_reports_count"],
                    parse_dt(s["created_at"]),
                    parse_dt(s["updated_at"]),
                ))

        execute_batch(cur, """
            INSERT INTO videos (
                id, creator_id, video_created_at,
                views_count, likes_count, comments_count, reports_count,
                created_at, updated_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING;
        """, videos_rows, page_size=500)

        execute_batch(cur, """
            INSERT INTO video_snapshots (
                id, video_id,
                views_count, likes_count, comments_count, reports_count,
                delta_views_count, delta_likes_count,
                delta_comments_count, delta_reports_count,
                created_at, updated_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING;
        """, snapshots_rows, page_size=1000)

    conn.close()
    print("JSON загружен")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.load_json path/to/videos.json")
        sys.exit(1)
    main(sys.argv[1])
