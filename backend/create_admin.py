"""Creates an admin account for the dashboard, or resets its password.

Usage (from backend/, venv active, DATABASE_URL set):
    python create_admin.py someone@alustudent.com
    python create_admin.py someone@alustudent.com reviewer

The password is typed twice and never shown. Only its hash is stored.
Running it again for the same email sets a new password.
"""
import getpass
import re
import sys

from werkzeug.security import generate_password_hash

from app.db import _get_conn

ROLES = ("admin", "reviewer")
MIN_PASSWORD_LENGTH = 10


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python create_admin.py EMAIL [admin|reviewer]")
        sys.exit(1)

    email = sys.argv[1].strip().lower()  # login lowercases the email too
    role = sys.argv[2] if len(sys.argv) == 3 else "admin"
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        print("That doesn't look like an email address.")
        sys.exit(1)
    if role not in ROLES:
        print("Role must be admin or reviewer.")
        sys.exit(1)

    password = getpass.getpass("Password (not shown): ")
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        sys.exit(1)
    if getpass.getpass("Same password again: ") != password:
        print("The two passwords don't match. Nothing was saved.")
        sys.exit(1)

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO admin_users (email, password_hash, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO UPDATE
                    SET password_hash = EXCLUDED.password_hash, role = EXCLUDED.role
                RETURNING id, (xmax = 0) AS created
                """,
                (email, generate_password_hash(password), role),
            )
            admin_id, created = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    action = "Created" if created else "Updated password for"
    print(f"{action} admin {admin_id}: {email} ({role}).")


if __name__ == "__main__":
    main()
