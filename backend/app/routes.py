from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/check", methods=["POST"])
def check():
    return jsonify({"status": "endpoint ready"})
