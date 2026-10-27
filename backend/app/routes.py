from flask import Blueprint, jsonify, request

from .rules import evaluate

api_bp = Blueprint("api", __name__)

VALID_CONTEXTS = {"job", "scholarship", "visa"}


@api_bp.route("/api/check", methods=["POST"])
def check():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    context = data.get("context", "job")

    if not text:
        return jsonify({"error": "text is required"}), 400
    if context not in VALID_CONTEXTS:
        return jsonify({"error": "context must be job, scholarship, or visa"}), 400

    result = evaluate(text, context)
    return jsonify(result)