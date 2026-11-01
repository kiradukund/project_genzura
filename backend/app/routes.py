import logging

from flask import Blueprint, jsonify, request

from .db import save_check
from .privacy import redact
from .rules import evaluate

log = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)

VALID_CONTEXTS = {"job", "scholarship", "visa"}
VALID_LANGUAGES = {"en", "rw"}


@api_bp.route("/api/check", methods=["POST"])
def check():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    context = data.get("context", "job")
    language = data.get("language", "en")

    if not text:
        return jsonify({"error": "text is required"}), 400
    if context not in VALID_CONTEXTS:
        return jsonify({"error": "context must be job, scholarship, or visa"}), 400
    if language not in VALID_LANGUAGES:
        return jsonify({"error": "language must be en or rw"}), 400

    # 1. rules on the RAW text  2. redact a copy  3. save the redacted copy
    result = evaluate(text, context)
    try:
        check_id = save_check(redact(text), context, result["risk_score"],
                              result["verdict"], result["flags"], "web", language)
    except Exception:
        log.exception("Could not save check")
        check_id = None

    return jsonify({**result, "check_id": check_id})
