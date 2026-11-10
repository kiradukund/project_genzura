"""Creates a partner API key and prints it once.

Usage (from backend/, venv active, DATABASE_URL in .env):
    python create_api_key.py "Partner name"
    python create_api_key.py "Partner name" 500     (custom daily limit)
"""
import secrets
import sys

from app.db import _get_conn
from app.partner import hash_key


def main():
    if len(sys.argv) < 2:
        print('Usage: python create_api_key.py "Partner name" [daily_limit]')
        sys.exit(1)
    name = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    key = "gz_" + secrets.token_urlsafe(32)
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO api_keys (partner_name, key_prefix, key_hash, daily_limit) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (name, key[:10], hash_key(key), limit),
            )
            key_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    print(f"Created key {key_id} for {name} (limit {limit}/day).")
    print("Give this key to the partner now. It is not stored and cannot be shown again:")
    print(key)


if __name__ == "__main__":
    main()
