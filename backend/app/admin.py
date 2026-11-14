from flask import Blueprint, jsonify

from .auth import require_admin
from .db import get_stats

admin_bp = Blueprint("admin", __name__)

# OWNER: Didier - Admin dashboard. Build: /api/admin/stats


@admin_bp.get("/api/admin/stats")
@require_admin
def admin_stats():
    try:
        return jsonify(get_stats())
    except Exception:
        return jsonify({"error": "stats unavailable"}), 503
