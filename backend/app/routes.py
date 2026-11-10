# OWNER: Abay
import logging

from flask import Blueprint, jsonify, request

from . import db
from .auth import attach_check, current_user_id, require_admin
from .integrations import send_sms, ussd_continue, ussd_end
from .lookup import apply_entity_flags, lookup as lookup_entities, record_report_entities
from .privacy import mask_text
from .rules import add_flag, evaluate

log = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

VALID_CONTEXTS = {"job", "scholarship", "visa"}
VALID_LANGUAGES = {"en", "rw"}
VALID_REPORT_STATUSES = {"new", "reviewing", "forwarded", "closed"}
MAX_TEXT_LENGTH = 2000

VERDICT_LABELS = {
    "low_risk": "LOW RISK: no major scam signs found. Still verify the sender.",
    "suspicious": "SUSPICIOUS: be careful. Do not pay or share personal details.",
    "high_risk": "HIGH RISK: likely a scam. Do not pay or reply.",
}


# ---------- helpers ----------

def _json_body():
    data = request.get_json(silent=True)
    return {} if data is None else data


def _text_from(data):
    """Return (text, error). error is the message for a 400, or None."""
    if not isinstance(data, dict):
        return None, "request body must be a JSON object"
    text = data.get("text")
    if text is None or (isinstance(text, str) and not text.strip()):
        return None, "text is required"
    if not isinstance(text, str):
        return None, "text must be a string"
    text = text.strip()
    if len(text) > MAX_TEXT_LENGTH:
        return None, f"text must be at most {MAX_TEXT_LENGTH} characters"
    return text, None


def _save_check(channel, context, language, text, result):
    """Persist a check without ever breaking the response if the DB is down."""
    try:
        return db.save_check(channel, context, language, mask_text(text), result)
    except Exception:
        log.exception("Could not save check")
        return None


def _evaluate(text, context):
    """Rule-based score, plus extra flags for risky entities and known contacts."""
    result = evaluate(text, context)
    try:
        for entity in db.find_risky_entities(text):
            if entity["status"] == "blacklisted":
                result = add_flag(result, "blacklisted_entity", 50)
            else:
                result = add_flag(result, "flagged_entity", 25)
    except Exception:
        log.exception("Entity name check failed; using rule score only")
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


# ---------- public: check ----------

@api_bp.route("/api/check", methods=["POST"])
def check():
    data = _json_body()
    text, error = _text_from(data)
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


# ---------- public: contact lookup ----------

@api_bp.route("/api/lookup", methods=["POST"])
def lookup_contacts():
    text, error = _text_from(_json_body())
    if error:
        return jsonify({"error": error}), 400
    try:
        entities = lookup_entities(text)
    except Exception:
        log.exception("Lookup failed")
        return jsonify({"error": "lookup unavailable"}), 503
    return jsonify({"entities": entities})


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
    data = _json_body()
    if not isinstance(data, dict):
        return jsonify({"error": "request body must be a JSON object"}), 400
    description = data.get("description")
    check_id = data.get("check_id")

    if not isinstance(description, str) or len(description.strip()) < 10:
        return jsonify({"error": "description must be at least 10 characters"}), 400
    description = description.strip()
    if len(description) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"description must be at most {MAX_TEXT_LENGTH} characters"}), 400
    if check_id is not None and (isinstance(check_id, bool) or not isinstance(check_id, int)):
        return jsonify({"error": "check_id must be an integer"}), 400

    try:
        report = db.create_report(mask_text(description), check_id)
    except Exception:
        log.exception("Could not create report")
        return jsonify({"error": "could not save report"}), 500

    # Count the report against every phone, email and link it mentions.
    # Best effort: the report itself is already saved.
    try:
        record_report_entities(description)
    except Exception:
        log.exception("Could not record report entities")
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


# ---------- admin (login lives in auth.py) ----------

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
    data = _json_body()
    status = data.get("status") if isinstance(data, dict) else None
    if not isinstance(status, str) or status not in VALID_REPORT_STATUSES:
        return jsonify({"error": "status must be new, reviewing, forwarded, or closed"}), 400
    report = db.update_report_status(report_id, status)
    if not report:
        return jsonify({"error": "report not found"}), 404
    return jsonify(report)