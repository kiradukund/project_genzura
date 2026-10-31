from flask import Blueprint, jsonify, request

from .rules import evaluate

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/check", methods=["POST"])
def check():
    # TODO (Abay): validate input (text required, context must be
    # job / scholarship / visa) and return HTTP 400 on bad input.
    data = request.get_json(silent=True) or {}
    result = evaluate(data.get("text", ""), data.get("context", "job"))
    return jsonify(result)
