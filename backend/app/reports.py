from flask import Blueprint, jsonify, request

from .db import _get_conn
from .privacy import redact
from .lookup import record_report_entities, hashed_entities

reports_bp = Blueprint("reports", __name__)

# OWNER: Chol - Report a scam, moderation, blocklist.
# Endpoints:
#   POST /api/reports                        — user submits a report
#   GET  /api/admin/reports                  — list reports by status (Didier calls this)
#   POST /api/admin/reports/<id>/approve     — approve and blacklist entities
#   POST /api/admin/reports/<id>/reject      — reject


@reports_bp.route("/api/reports", methods=["POST"])
def submit_report():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    check_id = data.get("check_id")
    contact = (data.get("contact") or "").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    masked_text = redact(text)
    masked_contact = redact(contact) if contact else None

    # count entities from the raw text before redacting
    record_report_entities(text)

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
    finally:
        conn.close()

    return jsonify({"report_id": report_id}), 201


@reports_bp.route("/api/admin/reports", methods=["GET"])
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
    finally:
        conn.close()

    reports = [
        {"id": r[0], "check_id": r[1], "masked_text": r[2],
         "contact": r[3], "status": r[4], "created_at": r[5].isoformat()}
        for r in rows
    ]
    return jsonify(reports)


@reports_bp.route("/api/admin/reports/<int:report_id>/approve", methods=["POST"])
def approve_report(report_id):
    data = request.get_json(silent=True) or {}
    admin_email = (data.get("admin_email") or "").strip()
    note = data.get("note", "")

    if not admin_email:
        return jsonify({"error": "admin_email is required"}), 400

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

            # blacklist all entities found in the report text
            masked_text = row[0]
            entities = hashed_entities(masked_text)
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
                "INSERT INTO audit_log (admin_email, action, report_id, note) VALUES (%s, 'approved', %s, %s)",
                (admin_email, report_id, note),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"status": "approved", "report_id": report_id})


@reports_bp.route("/api/admin/reports/<int:report_id>/reject", methods=["POST"])
def reject_report(report_id):
    data = request.get_json(silent=True) or {}
    admin_email = (data.get("admin_email") or "").strip()
    note = data.get("note", "")

    if not admin_email:
        return jsonify({"error": "admin_email is required"}), 400

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
                "INSERT INTO audit_log (admin_email, action, report_id, note) VALUES (%s, 'rejected', %s, %s)",
                (admin_email, report_id, note),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"status": "rejected", "report_id": report_id})
