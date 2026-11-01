import os
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

def _get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def save_check(masked_text: str, context: str, risk_score: int, verdict: str, flags: list, channel: str = "web", language: str = "en") -> int:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO checks (channel, context, language, masked_text, risk_score, verdict, flags)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (channel, context, language, masked_text, risk_score, verdict, Json(flags)),
            )
            return cur.fetchone()[0]
