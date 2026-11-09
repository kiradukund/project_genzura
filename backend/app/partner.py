import hashlib
import logging

from flask import Blueprint, jsonify, request

from .db import _get_conn, save_check
from .privacy import redact
from .routes import VALID_CONTEXTS, VALID_LANGUAGES
from .rules import evaluate

log = logging.getLogger(__name__)
partner_bp = Blueprint("partner", __name__)

MAX_TEXT_LENGTH = 2000


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def use_key(key: str):
    """Counts one request for this key and returns its row, or None if the key is unknown or disabled.

    The counter resets when the date changes. One UPDATE does both, so two
    requests at the same time cannot both slip past the limit.
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE api_keys
                SET requests_today = CASE WHEN usage_date = CURRENT_DATE
                                          THEN requests_today + 1 ELSE 1 END,
                    usage_date = CURRENT_DATE,
                    last_used_at = NOW()
                WHERE key_hash = %s AND active
                RETURNING id, partner_name, requests_today, daily_limit
                """,
                (hash_key(key),),
            )
            row = cur.fetchone()
        conn.commit()
    finally:
        conn.close()
    if row is None:
        return None
    return {"id": row[0], "partner_name": row[1], "requests_today": row[2], "daily_limit": row[3]}


@partner_bp.route("/v1/check", methods=["POST"])
def partner_check():
    key = request.headers.get("X-API-Key", "").strip()
    if not key:
        return jsonify({"error": "missing X-API-Key header"}), 401

    try:
        partner = use_key(key)
    except Exception:
        log.exception("Could not verify API key")
        return jsonify({"error": "service unavailable"}), 503
    if partner is None:
        return jsonify({"error": "invalid API key"}), 401
    if partner["requests_today"] > partner["daily_limit"]:
        return jsonify({"error": "daily limit reached"}), 429

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "body must be a JSON object"}), 400
    text = data.get("text")
    context = data.get("context", "job")
    language = data.get("language", "en")

    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "text is required"}), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"text must be at most {MAX_TEXT_LENGTH} characters"}), 400
    if not isinstance(context, str) or context not in VALID_CONTEXTS:
        return jsonify({"error": "context must be job, scholarship, or visa"}), 400
    if not isinstance(language, str) or language not in VALID_LANGUAGES:
        return jsonify({"error": "language must be en or rw"}), 400

    text = text.strip()
    result = evaluate(text, context)
    try:
        check_id = save_check(redact(text), context, result["risk_score"],
                              result["verdict"], result["flags"], "api", language)
    except Exception:
        log.exception("Could not save partner check")
        check_id = None

    remaining = max(partner["daily_limit"] - partner["requests_today"], 0)
    return jsonify({**result, "check_id": check_id, "requests_remaining_today": remaining})
