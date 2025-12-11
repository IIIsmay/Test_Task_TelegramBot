from datetime import date
from typing import Dict, Any
import logging

from app.db import fetchval

logger = logging.getLogger(__name__)


async def execute_query(query_struct: Dict[str, Any]) -> int:
    query_type = query_struct["query_type"]
    metric = query_struct.get("metric")
    filters = query_struct.get("filters", {})

    logger.info(
        "Execute query_type=%s metric=%s filters=%s",
        query_type,
        metric,
        filters,
    )

    if query_type == "count_videos":
        clauses = []
        params = []

        if filters.get("creator_id"):
            params.append(filters["creator_id"])
            clauses.append(f"creator_id = ${len(params)}")

        if filters.get("video_created_at_from"):
            params.append(date.fromisoformat(filters["video_created_at_from"]))
            clauses.append(f"video_created_at::date >= ${len(params)}")

        if filters.get("video_created_at_to"):
            params.append(date.fromisoformat(filters["video_created_at_to"]))
            clauses.append(f"video_created_at::date <= ${len(params)}")

        if filters.get("final_views_gt") is not None:
            params.append(filters["final_views_gt"])
            clauses.append(f"views_count > ${len(params)}")

        where = "WHERE " + " AND ".join(clauses) if clauses else ""

        return await fetchval(
            f"SELECT COUNT(*) FROM videos {where}",
            *params
        )

    if query_type == "sum_delta_metric":
        d = date.fromisoformat(filters["snapshot_date"])
        return await fetchval(
            f"""
            SELECT COALESCE(SUM(delta_{metric}_count), 0)
            FROM video_snapshots
            WHERE created_at::date = $1
            """,
            d,
        )

    if query_type == "count_distinct_videos_delta_gt_zero":
        d = date.fromisoformat(filters["snapshot_date"])
        return await fetchval(
            f"""
            SELECT COUNT(DISTINCT video_id)
            FROM video_snapshots
            WHERE created_at::date = $1
              AND delta_{metric}_count > 0
            """,
            d,
        )

    raise ValueError(f"Unknown query_type: {query_type}")
