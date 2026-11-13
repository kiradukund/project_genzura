import logging

from flask import Blueprint, jsonify, request

from .auth import require_admin
from .db import _get_conn
from .lookup import MAX_TEXT_LENGTH, hashed_entities, record_report_entities, text_from
from .privacy import redact

reports_bp = Blueprint("reports", __name__)

# OWNER: Chol - Report a scam, moderation, blocklist.
# Endpoints:
#   POST /api/reports                        — user submits a report
#   GET  /api/admin/reports                  — list reports by status (Didier calls this)
#   POST /api/admin/reports/<id>/approve     — approve and blacklist entities
#   POST /api/admin/reports/<id>/reject      — reject

log = logging.getLogger(__name__)

VALID_CONTEXTS = {"job", "scholarship", "visa"}


@reports_bp.route("/api/reports", methods=["POST"])
def submit_report():
    data = request.get_json(silent=True) or {}

    # same input checks as /api/check
    text, error = text_from(data)
    if error:
        return jsonify({"error": error}), 400

    context = data.get("context", "job")
    if not isinstance(context, str) or context not in VALID_CONTEXTS:
        return jsonify({"error": "context must be job, scholarship, or visa"}), 400

    check_id = data.get("check_id")
    contact = (data.get("contact") or "").strip()
    if contact and not isinstance(contact, str):
        return jsonify({"error": "contact must be a string"}), 400
    if contact and len(contact) > 200:
        return jsonify({"error": "contact must be at most 200 characters"}), 400

    masked_text = redact(text)
    masked_contact = redact(contact) if contact else None

    try:
        record_report_entities(text)
    except Exception:
        log.exception("Could not record report entities")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO report_submissions (check_id, masked_text, contact)
                VALUES (%s, %s, %s) RETURNING id
                """,
                (check_id, masked_text, masked_contact),
            )
            report_id = cur.fetchone()[0]
        conn.commit()
    except Exception:
        log.exception("Could not save report")
        return jsonify({"error": "service unavailable"}), 503
    finally:
        conn.close()

    return jsonify({"report_id": report_id}), 201


@reports_bp.route("/api/admin/reports", methods=["GET"])
@require_admin
def list_reports():
    status = request.args.get("status", "pending")
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, check_id, masked_text, contact, status, created_at
                FROM report_submissions WHERE status = %s ORDER BY created_at DESC
                """,
                (status,),
            )
            rows = cur.fetchall()
    except Exception:
        log.exception("Could not list reports")
        return jsonify({"error": "service unavailable"}), 503
    finally:
        conn.close()

    return jsonify([
        {"id": r[0], "check_id": r[1], "masked_text": r[2],
         "contact": r[3], "status": r[4], "created_at": r[5].isoformat()}
        for r in rows
    ])


@reports_bp.route("/api/admin/reports/<int:report_id>/approve", methods=["POST"])
@require_admin
def approve_report(report_id):
    # admin_email comes from the logged-in session, not the request body
    admin_id = request.admin["id"]
    data = request.get_json(silent=True) or {}
    note = data.get("note", "")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE report_submissions SET status = 'approved' WHERE id = %s RETURNING masked_text",
                (report_id,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "report not found"}), 404

            entities = hashed_entities(row[0])
            for e in entities:
                cur.execute(
                    """
                    INSERT INTO entities (kind, value_hash, report_count, status)
                    VALUES (%s, %s, 1, 'blacklisted')
                    ON CONFLICT (kind, value_hash) DO UPDATE
                    SET status = 'blacklisted', last_seen_at = NOW()
                    """,
                    (e["kind"], e["value_hash"]),
                )

            cur.execute(
                "INSERT INTO audit_log (admin_id, action, report_id, note) VALUES (%s, 'approved', %s, %s)",
                (admin_id, report_id, note),
            )
        conn.commit()
    except Exception:
        log.exception("Could not approve report")
        return jsonify({"error": "service unavailable"}), 503
    finally:
        conn.close()

    return jsonify({"status": "approved", "report_id": report_id})


@reports_bp.route("/api/admin/reports/<int:report_id>/reject", methods=["POST"])
@require_admin
def reject_report(report_id):
    # admin_email comes from the logged-in session, not the request body
    admin_id = request.admin["id"]
    data = request.get_json(silent=True) or {}
    note = data.get("note", "")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE report_submissions SET status = 'rejected' WHERE id = %s",
                (report_id,),
            )
            if cur.rowcount == 0:
                return jsonify({"error": "report not found"}), 404
            cur.execute(
                "INSERT INTO audit_log (admin_id, action, report_id, note) VALUES (%s, 'rejected', %s, %s)",
                (admin_id, report_id, note),
            )
        conn.commit()
    except Exception:
        log.exception("Could not reject report")
        return jsonify({"error": "service unavailable"}), 503
    finally:
        conn.close()

    return jsonify({"status": "rejected", "report_id": report_id})
