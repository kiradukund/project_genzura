import logging
from functools import wraps

from flask import Blueprint, current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash

from . import db
from .integrations import send_sms, ussd_continue, ussd_end
from .privacy import mask_text
from .rules import add_flag, evaluate

log = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

VALID_CONTEXTS = {"job", "scholarship", "visa"}
VALID_LANGUAGES = {"en", "rw"}
VALID_REPORT_STATUSES = {"new", "reviewing", "forwarded", "closed"}
TOKEN_MAX_AGE = 60 * 60 * 8  # 8 hours

VERDICT_LABELS = {
    "low_risk": "LOW RISK: no major scam signs found. Still verify the sender.",
    "suspicious": "SUSPICIOUS: be careful. Do not pay or share personal details.",
    "high_risk": "HIGH RISK: likely a scam. Do not pay or reply.",
}


# ---------- helpers ----------

def _save_check(channel, context, language, text, result):
    """Persist a check without ever breaking the response if the DB is down."""
    try:
        return db.save_check(channel, context, language, mask_text(text), result)
    except Exception:
        log.exception("Could not save check")
        return None


def _evaluate(text, context):
    """Rule-based score, plus extra flags if the text names a risky entity."""
    result = evaluate(text, context)
    try:
        for entity in db.find_risky_entities(text):
            if entity["status"] == "blacklisted":
                result = add_flag(result, "blacklisted_entity", 50)
            else:
                result = add_flag(result, "flagged_entity", 25)
    except Exception:
        log.exception("Entity check failed; using rule score only")
    return result


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="admin-auth")


def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "authentication required"}), 401
        try:
            request.admin = _serializer().loads(header[7:], max_age=TOKEN_MAX_AGE)
        except SignatureExpired:
            return jsonify({"error": "token expired"}), 401
        except BadSignature:
            return jsonify({"error": "invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper


# ---------- public: check ----------

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

    result = _evaluate(text, context)
    check_id = _save_check("web", context, language, text, result)
    return jsonify({**result, "check_id": check_id})


# ---------- public: verify entity ----------

@api_bp.route("/api/verify", methods=["GET"])
def verify_entity():
    q = (request.args.get("name") or "").strip()
    if len(q) < 2:
        return jsonify({"error": "name must be at least 2 characters"}), 400
    try:
        matches = db.find_entities(q)
    except Exception:
        log.exception("Entity lookup failed")
        return jsonify({"error": "lookup unavailable"}), 503
    return jsonify({"query": q, "matches": matches})


# ---------- public: report ----------

@api_bp.route("/api/report", methods=["POST"])
def create_report():
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    check_id = data.get("check_id")

    if len(description) < 10:
        return jsonify({"error": "description must be at least 10 characters"}), 400
    if check_id is not None and not isinstance(check_id, int):
        return jsonify({"error": "check_id must be an integer"}), 400

    try:
        report = db.create_report(mask_text(description), check_id)
    except Exception:
        log.exception("Could not create report")
        return jsonify({"error": "could not save report"}), 500
    return jsonify(report), 201


# ---------- channels: USSD and SMS (Africa's Talking callbacks) ----------

@api_bp.route("/api/ussd", methods=["POST"])
def ussd():
    """Africa's Talking posts `text` as the user's inputs joined with '*'."""
    raw = request.values.get("text", "")
    parts = raw.split("*") if raw else []
    contexts = {"1": "job", "2": "scholarship", "3": "visa"}

    if not parts:
        reply = ussd_continue(
            "Genzura scam check\n1. Job offer\n2. Scholarship\n3. Visa")
    elif parts[0] not in contexts:
        reply = ussd_end("Invalid choice. Please dial again.")
    elif len(parts) == 1:
        reply = ussd_continue("Type the message you received:")
    else:
        context = contexts[parts[0]]
        message = "*".join(parts[1:]).strip()
        result = _evaluate(message, context)
        _save_check("ussd", context, "en", message, result)
        reply = ussd_end(f"{VERDICT_LABELS[result['verdict']]} Score: {result['risk_score']}/100")

    return reply, 200, {"Content-Type": "text/plain"}


@api_bp.route("/api/sms", methods=["POST"])
def sms():
    """Inbound SMS. Format: '<JOB|SCHOLARSHIP|VISA> <message>' (default job)."""
    sender = request.values.get("from", "")
    body = (request.values.get("text") or "").strip()
    if not body:
        return "OK", 200

    first, _, rest = body.partition(" ")
    if first.lower() in VALID_CONTEXTS and rest.strip():
        context, message = first.lower(), rest.strip()
    else:
        context, message = "job", body

    result = _evaluate(message, context)
    _save_check("sms", context, "en", message, result)
    if sender:
        send_sms(sender, f"Genzura: {VERDICT_LABELS[result['verdict']]} Score {result['risk_score']}/100")
    return "OK", 200


# ---------- admin ----------

@api_bp.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    try:
        admin = db.get_admin_by_email(email)
    except Exception:
        log.exception("Admin lookup failed")
        return jsonify({"error": "service unavailable"}), 503

    if not admin or not check_password_hash(admin["password_hash"], password):
        return jsonify({"error": "invalid credentials"}), 401

    token = _serializer().dumps({"id": admin["id"], "role": admin["role"]})
    return jsonify({"token": token, "role": admin["role"]})


@api_bp.route("/api/admin/stats", methods=["GET"])
@require_admin
def admin_stats():
    return jsonify(db.get_stats())


@api_bp.route("/api/admin/reports", methods=["GET"])
@require_admin
def admin_reports():
    status = request.args.get("status")
    if status and status not in VALID_REPORT_STATUSES:
        return jsonify({"error": "invalid status"}), 400
    limit = min(request.args.get("limit", 50, type=int), 200)
    offset = max(request.args.get("offset", 0, type=int), 0)
    return jsonify(db.list_reports(status, limit, offset))


@api_bp.route("/api/admin/reports/<int:report_id>", methods=["PATCH"])
@require_admin
def admin_update_report(report_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in VALID_REPORT_STATUSES:
        return jsonify({"error": "status must be new, reviewing, forwarded, or closed"}), 400
    report = db.update_report_status(report_id, status)
    if not report:
        return jsonify({"error": "report not found"}), 404
    return jsonify(report)