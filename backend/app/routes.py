# OWNER: Abay
"""Abay's route: /api/check. (/api/lookup lives in lookup.py as `lookup_bp`.)

USSD, SMS and report routes live in Kuol's and Chol's own files. Admin and
moderation endpoints can use `require_admin` from auth.py.

Everything imported by name here exists on dev (evaluate, redact, and my own
lookup/auth modules). Functions on `db` are looked up when a request runs, so a
missing one can only fail that one call (it is caught), never the app startup.
"""
import logging

from flask import Blueprint, jsonify, request

from . import db
from .auth import attach_check, current_user_id
from .lookup import MAX_TEXT_LENGTH, apply_entity_flags, text_from  # noqa: F401
from .privacy import redact
from .rules import evaluate

log = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

VALID_CONTEXTS = {"job", "scholarship", "visa"}
VALID_LANGUAGES = {"en", "rw"}


# ---------- helpers ----------

def _json_body():
    data = request.get_json(silent=True)
    return {} if data is None else data


def _check_id(saved):
    """Chol's save_check may return the new id or a row: accept both."""
    if isinstance(saved, bool):
        return None
    if isinstance(saved, int):
        return saved
    if isinstance(saved, dict) and isinstance(saved.get("id"), int):
        return saved["id"]
    return None


def _save_check(channel, context, language, text, result):
    """Save through Chol's db.save_check without ever breaking the response.

    The text is passed through redact() first, so only redacted text is stored.
    """
    try:
        saved = db.save_check(
            channel=channel,
            context=context,
            language=language,
            masked_text=redact(text),
            risk_score=result["risk_score"],
            verdict=result["verdict"],
            flags=result["flags"],
        )
    except Exception:
        log.exception("Could not save check")
        return None
    return _check_id(saved)


def _evaluate(text, context):
    """Rule-based score, plus a flag when a phone, email or link is already known."""
    result = evaluate(text, context)
    try:
        result = apply_entity_flags(result, text)
    except Exception:
        log.exception("Contact lookup failed; using rule score only")
    return result


def _link_check_to_user(check_id, user_id):
    try:
        attach_check(check_id, user_id)
    except Exception:
        log.exception("Could not link check to user")


# ---------- check ----------

@api_bp.route("/api/check", methods=["POST"])
def check():
    data = _json_body()
    text, error = text_from(data)
    if error:
        return jsonify({"error": error}), 400

    context = data.get("context", "job")
    language = data.get("language", "en")
    if not isinstance(context, str):
        return jsonify({"error": "context must be a string"}), 400
    if not isinstance(language, str):
        return jsonify({"error": "language must be a string"}), 400
    if context not in VALID_CONTEXTS:
        return jsonify({"error": "context must be job, scholarship, or visa"}), 400
    if language not in VALID_LANGUAGES:
        return jsonify({"error": "language must be en or rw"}), 400

    result = _evaluate(text, context)
    check_id = _save_check("web", context, language, text, result)

    user_id = current_user_id()  # signed-in users see this check in "My checks"
    if check_id and user_id:
        _link_check_to_user(check_id, user_id)

    return jsonify({**result, "check_id": check_id})