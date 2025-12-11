import logging
from datetime import date, time
from typing import Dict, Any, Optional

from app.db import fetchval

logger = logging.getLogger(__name__)


# --------------------------------------
# Helpers
# --------------------------------------
def _parse_date(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    return date.fromisoformat(d)


def _parse_time(t: Optional[str]) -> Optional[time]:
    if not t:
        return None
    return time.fromisoformat(t)


# --------------------------------------
# Main executor
# --------------------------------------
async def execute_query(q: Dict[str, Any]) -> int:
    qtype = q["query_type"]
    metric = q.get("metric")
    f = q.get("filters", {})

    logger.info("Execute query_type=%s metric=%s filters=%s", qtype, metric, f)

    # --------------------------------------
    # 1) COUNT VIDEOS
    # --------------------------------------
    if qtype == "count_videos":
        clauses = []
        params = []

        if f.get("creator_id"):
            params.append(f["creator_id"])
            clauses.append(f"creator_id = ${len(params)}")

        if f.get("video_created_at_from"):
            params.append(_parse_date(f["video_created_at_from"]))
            clauses.append(f"video_created_at::date >= ${len(params)}")

        if f.get("video_created_at_to"):
            params.append(_parse_date(f["video_created_at_to"]))
            clauses.append(f"video_created_at::date <= ${len(params)}")

        if f.get("final_views_gt") is not None:
            params.append(f["final_views_gt"])
            clauses.append(f"views_count > ${len(params)}")

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return await fetchval(f"SELECT COUNT(*) FROM videos {where}", *params)

    # --------------------------------------
    # 2) SUM FINAL METRIC
    # --------------------------------------
    if qtype == "sum_final_metric":
        clauses = []
        params = []

        if f.get("creator_id"):
            params.append(f["creator_id"])
            clauses.append(f"creator_id = ${len(params)}")

        if f.get("video_created_at_from"):
            params.append(_parse_date(f["video_created_at_from"]))
            clauses.append(f"video_created_at::date >= ${len(params)}")

        if f.get("video_created_at_to"):
            params.append(_parse_date(f["video_created_at_to"]))
            clauses.append(f"video_created_at::date <= ${len(params)}")

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return await fetchval(
            f"SELECT COALESCE(SUM({metric}_count), 0) FROM videos {where}", *params
        )

    # --------------------------------------
    # 3) SUM DELTA IN ONE DAY
    # --------------------------------------
    if qtype == "sum_delta_metric":
        d = _parse_date(f["snapshot_date"])
        return await fetchval(
            f"""
            SELECT COALESCE(SUM(delta_{metric}_count), 0)
            FROM video_snapshots
            WHERE created_at::date = $1
            """,
            d,
        )

    # --------------------------------------
    # 4) COUNT DISTINCT VIDEOS WITH POSITIVE DELTA
    # --------------------------------------
    if qtype == "count_distinct_videos_delta_gt_zero":
        d = _parse_date(f["snapshot_date"])
        return await fetchval(
            f"""
            SELECT COUNT(DISTINCT video_id)
            FROM video_snapshots
            WHERE created_at::date = $1
              AND delta_{metric}_count > 0
            """,
            d,
        )

    # --------------------------------------
    # 5) INTERVAL SUM (THE FIX FOR 757!)
    # --------------------------------------
    if qtype == "sum_delta_metric_interval":
        d = _parse_date(f["snapshot_date"])
        t1 = _parse_time(f.get("snapshot_time_from"))
        t2 = _parse_time(f.get("snapshot_time_to"))
        creator = f.get("creator_id")

        params = [d]
        clauses = ["s.created_at::date = $1"]

        if t1:
            params.append(t1)
            clauses.append(f"s.created_at::time >= ${len(params)}")

        if t2:
            params.append(t2)
            clauses.append(f"s.created_at::time <= ${len(params)}")

        if creator:
            params.append(creator)
            clauses.append(f"v.creator_id = ${len(params)}")

        return await fetchval(
            f"""
            SELECT COALESCE(SUM(s.delta_{metric}_count), 0)
            FROM video_snapshots s
            JOIN videos v ON v.id = s.video_id
            WHERE {" AND ".join(clauses)}
            """,
            *params,
        )

    # --------------------------------------
    # 6) COUNT NEGATIVE DELTAS (FIX FOR 24)
    # --------------------------------------
    if qtype == "count_negative_deltas":
        return await fetchval(
            f"""
            SELECT COUNT(*)
            FROM video_snapshots
            WHERE delta_{metric}_count < 0
            """
        )

    # --------------------------------------
    # UNKNOWN
    # --------------------------------------
    raise ValueError(f"Unknown query_type: {qtype}")
