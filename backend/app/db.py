# PostgreSQL connection helpers go here
"""PostgreSQL connection helpers and queries for Genzura."""
import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import Json, RealDictCursor


@contextmanager
def get_conn():
    """Open a connection, commit on success, roll back on error, always close."""
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _run(sql, params=None, fetch="all"):
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params or ())
        if fetch == "all":
            return cur.fetchall()
        if fetch == "one":
            return cur.fetchone()
        return None


# ---------- checks ----------

def save_check(channel, context, language, masked_text, result):
    row = _run(
        """INSERT INTO checks (channel, context, language, masked_text,
                               risk_score, verdict, flags)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (channel, context, language, masked_text,
         result["risk_score"], result["verdict"], Json(result["flags"])),
        fetch="one",
    )
    return row["id"]


# ---------- reports ----------

def create_report(description, check_id=None):
    return _run(
        """INSERT INTO reports (check_id, description)
           VALUES (%s, %s) RETURNING id, status, created_at""",
        (check_id, description),
        fetch="one",
    )


def list_reports(status=None, limit=50, offset=0):
    if status:
        return _run(
            """SELECT * FROM reports WHERE status = %s
               ORDER BY created_at DESC LIMIT %s OFFSET %s""",
            (status, limit, offset),
        )
    return _run(
        "SELECT * FROM reports ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset),
    )


def update_report_status(report_id, status):
    return _run(
        "UPDATE reports SET status = %s WHERE id = %s RETURNING *",
        (status, report_id),
        fetch="one",
    )


# ---------- verified entities ----------

def find_entities(query, limit=10):
    return _run(
        """SELECT id, name, type, website, status, notes
           FROM verified_entities
           WHERE name ILIKE %s ORDER BY name LIMIT %s""",
        (f"%{query}%", limit),
    )


def find_risky_entities(text):
    """Flagged/blacklisted entities whose name appears in the text."""
    return _run(
        """SELECT name, status FROM verified_entities
           WHERE status IN ('flagged', 'blacklisted')
             AND position(lower(name) in lower(%s)) > 0""",
        (text,),
    )


# ---------- admin ----------

def get_admin_by_email(email):
    return _run(
        "SELECT id, email, password_hash, role FROM admin_users WHERE email = %s",
        (email.lower().strip(),),
        fetch="one",
    )


def get_stats():
    return {
        "total_checks": _run("SELECT COUNT(*) AS n FROM checks", fetch="one")["n"],
        "by_verdict": _run(
            "SELECT verdict, COUNT(*) AS n FROM checks GROUP BY verdict"),
        "by_channel": _run(
            "SELECT channel, COUNT(*) AS n FROM checks GROUP BY channel"),
        "by_context": _run(
            "SELECT context, COUNT(*) AS n FROM checks GROUP BY context"),
        "reports_by_status": _run(
            "SELECT status, COUNT(*) AS n FROM reports GROUP BY status"),
        "last_7_days": _run(
            """SELECT created_at::date AS day, COUNT(*) AS n
               FROM checks WHERE created_at >= NOW() - INTERVAL '7 days'
               GROUP BY day ORDER BY day"""),
    }