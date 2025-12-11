from datetime import date
from typing import Dict, Any

from app.db import fetchval


async def execute_query(query_struct: Dict[str, Any]) -> int:
    query_type = query_struct["query_type"]
    metric = query_struct.get("metric")
    filters = query_struct.get("filters", {})

    # =========================
    # 1. Сколько всего видео
    # =========================
    if query_type == "count_videos":
        where_clauses = []
        params = []

        creator_id = filters.get("creator_id")
        if creator_id:
            params.append(creator_id)
            where_clauses.append(f"creator_id = ${len(params)}")

        date_from = filters.get("video_created_at_from")
        if date_from:
            params.append(date.fromisoformat(date_from))
            where_clauses.append(f"video_created_at::date >= ${len(params)}")

        date_to = filters.get("video_created_at_to")
        if date_to:
            params.append(date.fromisoformat(date_to))
            where_clauses.append(f"video_created_at::date <= ${len(params)}")

        final_views_gt = filters.get("final_views_gt")
        if final_views_gt is not None:
            params.append(final_views_gt)
            where_clauses.append(f"views_count > ${len(params)}")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        sql = f"""
            SELECT COUNT(*)
            FROM videos
            {where_sql}
        """
        return await fetchval(sql, *params)

    # ==========================================
    # 2. На сколько <metric> выросли за дату
    # ==========================================
    elif query_type == "sum_delta_metric":
        if not metric:
            raise ValueError("metric обязателен для sum_delta_metric")

        snapshot_date = filters.get("snapshot_date")
        if not snapshot_date:
            raise ValueError("snapshot_date обязателен")

        snapshot_date = date.fromisoformat(snapshot_date)

        sql = f"""
            SELECT COALESCE(SUM(delta_{metric}_count), 0)
            FROM video_snapshots
            WHERE created_at::date = $1
        """
        return await fetchval(sql, snapshot_date)

    # =========================================================
    # 3. Сколько разных видео имели приращение > 0 за дату
    # =========================================================
    elif query_type == "count_distinct_videos_delta_gt_zero":
        if not metric:
            raise ValueError("metric обязателен")

        snapshot_date = filters.get("snapshot_date")
        if not snapshot_date:
            raise ValueError("snapshot_date обязателен")

        snapshot_date = date.fromisoformat(snapshot_date)

        sql = f"""
            SELECT COUNT(DISTINCT video_id)
            FROM video_snapshots
            WHERE created_at::date = $1
              AND delta_{metric}_count > 0
        """
        return await fetchval(sql, snapshot_date)

    # =========================
    # 4. Неизвестный тип
    # =========================
    else:
        raise ValueError(f"Неизвестный query_type: {query_type}")
