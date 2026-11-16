# OWNER: Alier - Trending scams. Build: GET /api/trends
import logging

from flask import Blueprint, jsonify, request

from .db import _get_conn

log = logging.getLogger(__name__)
trends_bp = Blueprint("trends", __name__)

ALLOWED_DAYS = (7, 30)
# Below this many checks in the period, the page says "Not enough data yet".
MIN_TOTAL = 20
# A red flag or offer type seen fewer times than this is hidden (privacy).
MIN_COUNT = 5


def fetch_counts(days):
    """Counts from the checks table for the last `days` days. Counts only, never message text.

    Returns (total, {flag_id: count}, {context: count}).
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            period = "created_at >= NOW() - make_interval(days => %s)"
            cur.execute(f"SELECT COUNT(*) FROM checks WHERE {period}", (days,))
            total = cur.fetchone()[0]
            cur.execute(
                f"""
                SELECT flag, COUNT(*) FROM checks, jsonb_array_elements_text(flags) AS flag
                WHERE {period}
                GROUP BY flag
                """,
                (days,),
            )
            flags = dict(cur.fetchall())
            cur.execute(f"SELECT context, COUNT(*) FROM checks WHERE {period} GROUP BY context", (days,))
            contexts = dict(cur.fetchall())
    finally:
        conn.close()
    return total, flags, contexts


def _ranked(counts):
    """Items seen at least MIN_COUNT times, most common first."""
    items = [{"id": key, "count": n} for key, n in counts.items() if n >= MIN_COUNT]
    return sorted(items, key=lambda item: (-item["count"], item["id"]))


def build_trends(days, total, flags, contexts):
    enough = total >= MIN_TOTAL
    return {
        "days": days,
        "total": total,
        "enough_data": enough,
        # With too little data, show no numbers at all (they would be misleading).
        "flags": _ranked(flags) if enough else [],
        "contexts": _ranked(contexts) if enough else [],
    }


@trends_bp.route("/api/trends", methods=["GET"])
def trends():
    try:
        days = int(request.args.get("days", 7))
    except ValueError:
        days = None
    if days not in ALLOWED_DAYS:
        return jsonify({"error": "days must be 7 or 30"}), 400

    try:
        total, flags, contexts = fetch_counts(days)
    except Exception:
        log.exception("Could not load trends")
        return jsonify({"error": "trends unavailable"}), 503

    return jsonify(build_trends(days, total, flags, contexts))
