import os
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()


def _get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def save_check(masked_text: str, context: str, risk_score: int, verdict: str, flags: list, channel: str = "web", language: str = "en") -> int:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO checks (channel, context, language, masked_text, risk_score, verdict, flags)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (channel, context, language, masked_text, risk_score, verdict, Json(flags)),
            )
            row_id = cur.fetchone()[0]
        conn.commit()
        return row_id
    finally:
        conn.close()


def get_stats() -> dict:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM checks")
            total = cur.fetchone()[0]
            cur.execute("SELECT verdict, COUNT(*) FROM checks GROUP BY verdict")
            by_verdict = dict(cur.fetchall())
            cur.execute("SELECT context, COUNT(*) FROM checks GROUP BY context")
            by_context = dict(cur.fetchall())
            cur.execute("""
                SELECT flag, COUNT(*) AS n FROM checks,
                jsonb_array_elements_text(flags) AS flag
                GROUP BY flag ORDER BY n DESC LIMIT 5
            """)
            top_flags = [{"flag": f, "count": n} for f, n in cur.fetchall()]
            cur.execute("""
                SELECT DATE(created_at AT TIME ZONE 'Africa/Kigali') AS day, COUNT(*)
                FROM checks WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY day ORDER BY day
            """)
            per_day = [{"day": str(d), "count": n} for d, n in cur.fetchall()]
    finally:
        conn.close()
    return {
        "total": total,
        "by_verdict": by_verdict,
        "by_context": by_context,
        "top_flags": top_flags,
        "per_day": per_day,
    }
