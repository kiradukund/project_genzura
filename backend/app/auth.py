# OWNER: Abay
"""Accounts.

1. Admin login (email + password against admin_users) for the dashboard.
2. Phone + SMS code sign-in for everyone else.

Rules:
- A phone number is only ever stored as a keyed hash (HMAC-SHA256 with
  PHONE_HASH_KEY). The real number exists in memory just long enough to send
  the SMS.
- A code expires after 5 minutes, allows 3 guesses in total, and a phone can
  request at most 3 codes per hour.
- The session is a signed token in an httpOnly cookie. JavaScript never sees it.
- DELETE /api/auth/account removes the user, their checks and pending codes.

All database access goes through the small `_store_*` functions, which use
`_get_conn()` from db.py (a psycopg2 connection) and take timestamps from
Python so the 5-minute and 1-hour rules are testable.
"""
import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, current_app, jsonify, request
from itsdangerous import BadData, URLSafeTimedSerializer
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash

from .db import _get_conn
from .integrations import send_sms
from .lookup import normalize_phone

log = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

COOKIE_NAME = "genzura_session"
CODE_TTL = timedelta(minutes=5)
MAX_ATTEMPTS = 3
MAX_REQUESTS_PER_HOUR = 3
REQUEST_WINDOW = timedelta(hours=1)
SESSION_MAX_AGE = {"admin": 8 * 3600, "user": 7 * 24 * 3600}  # seconds

# Spent on unknown emails so a wrong email and a wrong password take equally long.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


# ---------- small helpers ----------

def _now():
    return datetime.now(timezone.utc)


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _hash_key():
    key = os.getenv("PHONE_HASH_KEY")
    if not key:
        raise RuntimeError("PHONE_HASH_KEY is not set")
    return key.encode()


def phone_hash(e164):
    return hmac.new(_hash_key(), f"phone:{e164}".encode(), hashlib.sha256).hexdigest()


def code_hash(phone_digest, code):
    return hmac.new(_hash_key(), f"code:{phone_digest}:{code}".encode(), hashlib.sha256).hexdigest()


# ---------- session cookie ----------

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="session")


def _cookie_options():
    return {
        "httponly": True,
        "secure": os.getenv("COOKIE_SECURE", "true").lower() != "false",
        "samesite": os.getenv("COOKIE_SAMESITE", "Lax"),
        "path": "/",
    }


def _start_session(resp, kind, **payload):
    token = _serializer().dumps({"k": kind, **payload})
    resp.set_cookie(COOKIE_NAME, token, max_age=SESSION_MAX_AGE[kind], **_cookie_options())
    return resp


def _end_session(resp):
    resp.delete_cookie(COOKIE_NAME, **_cookie_options())
    return resp


def current_session():
    """The signed-in session ({"k": "admin"|"user", ...}) or None."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload, issued_at = _serializer().loads(token, return_timestamp=True)
    except BadData:
        return None
    kind = payload.get("k") if isinstance(payload, dict) else None
    if kind not in SESSION_MAX_AGE:
        return None
    if (_now() - issued_at).total_seconds() > SESSION_MAX_AGE[kind]:
        return None
    return payload


def current_user_id():
    """Id of the signed-in user, or None (admins and visitors have none)."""
    session = current_session()
    return session.get("id") if session and session["k"] == "user" else None


def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        session = current_session()
        if not session:
            return jsonify({"error": "authentication required"}), 401
        if session["k"] != "admin":
            return jsonify({"error": "admin access required"}), 403
        request.admin = session
        return f(*args, **kwargs)
    return wrapper


def require_user(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        session = current_session()
        if not session or session["k"] != "user":
            return jsonify({"error": "authentication required"}), 401
        try:
            user = _store_get_user(session["id"])
        except Exception:
            log.exception("User lookup failed")
            return jsonify({"error": "service unavailable"}), 503
        if not user:  # e.g. the account was deleted
            return _end_session(jsonify({"error": "authentication required"})), 401
        request.user = user
        return f(*args, **kwargs)
    return wrapper


# ---------- database ----------

def _exec(sql, params=(), fetch=None):
    conn = _get_conn()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch == "one":
                return cur.fetchone()
            if fetch == "all":
                return cur.fetchall()
            return cur.rowcount
    finally:
        conn.close()


def _store_get_admin(email):
    return _exec(
        "SELECT id, email, password_hash, role FROM admin_users WHERE email = %s",
        (email,), "one")


def _store_count_recent_requests(phone_digest, since):
    row = _exec(
        "SELECT COUNT(*) AS n FROM sms_codes WHERE phone_hash = %s AND created_at >= %s",
        (phone_digest, since), "one")
    return row["n"]


def _store_create_code(phone_digest, code_digest, created_at, expires_at):
    row = _exec(
        """INSERT INTO sms_codes (phone_hash, code_hash, created_at, expires_at)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (phone_digest, code_digest, created_at, expires_at), "one")
    return row["id"]


def _store_delete_code(code_id):
    _exec("DELETE FROM sms_codes WHERE id = %s", (code_id,))


def _store_claim_attempt(phone_digest, now, max_attempts):
    """Use up one guess on the newest live code. One atomic statement, so
    parallel requests cannot squeeze in more than max_attempts guesses."""
    return _exec(
        """UPDATE sms_codes SET attempts = attempts + 1
           WHERE id = (SELECT id FROM sms_codes
                       WHERE phone_hash = %s AND used_at IS NULL AND expires_at > %s
                       ORDER BY created_at DESC LIMIT 1)
             AND attempts < %s
           RETURNING id, code_hash, attempts""",
        (phone_digest, now, max_attempts), "one")


def _store_mark_code_used(code_id, now):
    return _exec(
        "UPDATE sms_codes SET used_at = %s WHERE id = %s AND used_at IS NULL",
        (now, code_id)) == 1


def _store_upsert_user(phone_digest, now):
    row = _exec(
        """INSERT INTO users (phone_hash, created_at, last_login_at)
           VALUES (%s, %s, %s)
           ON CONFLICT (phone_hash) DO UPDATE SET last_login_at = EXCLUDED.last_login_at
           RETURNING id""",
        (phone_digest, now, now), "one")
    return row["id"]


def _store_get_user(user_id):
    return _exec("SELECT id, created_at FROM users WHERE id = %s", (user_id,), "one")


def _store_delete_user(user_id):
    """Delete the user (their checks go with them: ON DELETE CASCADE) and any codes."""
    conn = _get_conn()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM users WHERE id = %s RETURNING phone_hash", (user_id,))
            row = cur.fetchone()
            if not row:
                return False
            cur.execute("DELETE FROM sms_codes WHERE phone_hash = %s", (row["phone_hash"],))
            return True
    finally:
        conn.close()


def _store_user_checks(user_id, limit, offset):
    return _exec(
        """SELECT id, channel, context, language, masked_text, risk_score,
                  verdict, flags, created_at
           FROM checks WHERE user_id = %s
           ORDER BY created_at DESC LIMIT %s OFFSET %s""",
        (user_id, limit, offset), "all")


def attach_check(check_id, user_id):
    """Link a saved check to the signed-in user (used by /api/check)."""
    _exec("UPDATE checks SET user_id = %s WHERE id = %s", (user_id, check_id))


# ---------- admin login ----------

@auth_bp.route("/api/auth/admin/login", methods=["POST"])
@auth_bp.route("/api/admin/login", methods=["POST"])  # path the first version used
def admin_login():
    data = _json_body()
    email = data.get("email")
    password = data.get("password")
    if (not isinstance(email, str) or not isinstance(password, str)
            or not email.strip() or not password):
        return jsonify({"error": "email and password are required"}), 400

    try:
        admin = _store_get_admin(email.lower().strip())
    except Exception:
        log.exception("Admin lookup failed")
        return jsonify({"error": "service unavailable"}), 503

    password_ok = check_password_hash(admin["password_hash"] if admin else _DUMMY_HASH, password)
    if not admin or not password_ok:
        return jsonify({"error": "invalid credentials"}), 401

    resp = jsonify({"role": admin["role"]})
    return _start_session(resp, "admin", id=admin["id"], role=admin["role"])


# ---------- phone + SMS code ----------

@auth_bp.route("/api/auth/phone/request", methods=["POST"])
def phone_request():
    phone = _json_body().get("phone")
    e164 = normalize_phone(phone) if isinstance(phone, str) else None
    if not e164:
        return jsonify({"error": "enter a valid phone number"}), 400

    now = _now()
    try:
        digest = phone_hash(e164)
        if _store_count_recent_requests(digest, now - REQUEST_WINDOW) >= MAX_REQUESTS_PER_HOUR:
            return jsonify({"error": "too many codes requested, try again in an hour"}), 429
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_id = _store_create_code(digest, code_hash(digest, code), now, now + CODE_TTL)
    except Exception:
        log.exception("Could not create SMS code")
        return jsonify({"error": "service unavailable"}), 503

    minutes = int(CODE_TTL.total_seconds() // 60)
    if not send_sms(e164, f"Your Genzura code is {code}. It expires in {minutes} minutes."):
        try:  # a code nobody received must not use up the person's hourly allowance
            _store_delete_code(code_id)
        except Exception:
            log.exception("Could not remove unsent code")
        return jsonify({"error": "could not send the SMS, try again"}), 502

    return jsonify({"message": "code sent", "expires_in": int(CODE_TTL.total_seconds())})


@auth_bp.route("/api/auth/phone/verify", methods=["POST"])
def phone_verify():
    data = _json_body()
    phone, code = data.get("phone"), data.get("code")
    e164 = normalize_phone(phone) if isinstance(phone, str) else None
    if not e164 or not isinstance(code, str) or not re.fullmatch(r"\d{6}", code):
        return jsonify({"error": "phone and a 6-digit code are required"}), 400

    now = _now()
    invalid = {"error": "invalid or expired code"}
    try:
        digest = phone_hash(e164)
        claimed = _store_claim_attempt(digest, now, MAX_ATTEMPTS)
        if not claimed:  # no live code, expired, or all guesses used
            return jsonify(invalid), 400
        if not hmac.compare_digest(claimed["code_hash"], code_hash(digest, code)):
            return jsonify({**invalid, "attempts_left": MAX_ATTEMPTS - claimed["attempts"]}), 400
        if not _store_mark_code_used(claimed["id"], now):  # already used by a parallel request
            return jsonify(invalid), 400
        user_id = _store_upsert_user(digest, now)
    except Exception:
        log.exception("Code verification failed")
        return jsonify({"error": "service unavailable"}), 503

    return _start_session(jsonify({"signed_in": True}), "user", id=user_id)


# ---------- session and account ----------

@auth_bp.route("/api/auth/me", methods=["GET"])
def me():
    session = current_session()
    if not session:
        return jsonify({"error": "authentication required"}), 401
    if session["k"] == "admin":
        return jsonify({"kind": "admin", "role": session.get("role")})
    try:
        user = _store_get_user(session["id"])
    except Exception:
        log.exception("User lookup failed")
        return jsonify({"error": "service unavailable"}), 503
    if not user:
        return _end_session(jsonify({"error": "authentication required"})), 401
    return jsonify({"kind": "user", "created_at": user["created_at"]})


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    return _end_session(jsonify({"signed_out": True}))


@auth_bp.route("/api/auth/account", methods=["DELETE"])
@require_user
def delete_account():
    try:
        deleted = _store_delete_user(request.user["id"])
    except Exception:
        log.exception("Could not delete account")
        return jsonify({"error": "could not delete account"}), 500
    return _end_session(jsonify({"deleted": deleted}))


@auth_bp.route("/api/me/checks", methods=["GET"])
@require_user
def my_checks():
    limit = min(max(request.args.get("limit", 50, type=int), 1), 100)
    offset = max(request.args.get("offset", 0, type=int), 0)
    try:
        checks = _store_user_checks(request.user["id"], limit, offset)
    except Exception:
        log.exception("Could not load checks")
        return jsonify({"error": "service unavailable"}), 503
    return jsonify({"checks": checks, "limit": limit, "offset": offset})