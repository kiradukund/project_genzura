# OWNER: Kuol - Scam trend alerts by SMS
"""Weekly scam alerts.

POST /api/alerts/subscribe     {"phone", "language"}   -> {"subscribed": true}
POST /api/alerts/unsubscribe   {"phone"}               -> {"unsubscribed": true}
POST /api/alerts/send-weekly   header X-Cron-Token     -> {"sent": n, "failed": n}
    Called once a week by a scheduler (e.g. cron-job.org or a GitHub Action).
    Needs ALERTS_CRON_TOKEN in backend/.env; without it the endpoint is off.

People can also reply STOP to any alert (handled in sms.py).
Table: alert_subscribers (db/migrations/006_alerts.sql).
"""
import hmac
import logging
import os

from flask import Blueprint, jsonify, request

from . import messages
from .db import _get_conn
from .sms import RateLimiter, SmsError, is_configured, normalize_phone, send_sms

log = logging.getLogger(__name__)
alerts_bp = Blueprint("alerts", __name__)

# Alier: please review the wording and the Kinyarwanda (GSM-7, max 160 characters).
ALERT_TEXT = {
    "en": {
        "welcome": "Genzura: you will get a weekly scam alert. Never pay before you verify. Reply STOP to end.",
        "weekly": "Genzura alert: {count} risky offers checked this week. Top sign: {reason}. Never pay first. RIB 166. STOP to end",
        "quiet": "Genzura alert: few scams reported this week. Still, never pay before you verify. RIB 166. STOP to end",
    },
    "rw": {
        "welcome": "Genzura: uzajya ubona ubutumwa buri cyumweru ku buriganya. Ntukishyure utagenzuye. Ohereza STOP uhagarike.",
        "weekly": "Genzura: amatangazo {count} ateye inkeke iki cyumweru. Ikimenyetso: {reason}. Ntukishyure. RIB 166. STOP",
        "quiet": "Genzura: uburiganya buke iki cyumweru. Ariko ntukishyure utagenzuye. RIB 166. STOP uhagarike",
    },
}

subscribe_limiter = RateLimiter(3, 60 * 60)


# ---- database ---------------------------------------------------------------

def save_subscriber(phone, language):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alert_subscribers (phone, language) VALUES (%s, %s)
                ON CONFLICT (phone) DO UPDATE
                SET language = EXCLUDED.language, active = TRUE, unsubscribed_at = NULL
                """,
                (phone, language),
            )
        conn.commit()
    finally:
        conn.close()


def unsubscribe(phone):
    """Turn alerts off for this number. Returns True if it was subscribed."""
    phone = normalize_phone(phone)
    if phone is None:
        return False
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE alert_subscribers SET active = FALSE, unsubscribed_at = NOW()
                WHERE phone = %s AND active
                """,
                (phone,),
            )
            changed = cur.rowcount > 0
        conn.commit()
    finally:
        conn.close()
    return changed


def active_subscribers():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, phone, language FROM alert_subscribers WHERE active ORDER BY id")
            return [{"id": r[0], "phone": r[1], "language": r[2]} for r in cur.fetchall()]
    finally:
        conn.close()


def weekly_summary():
    """Risky checks in the last 7 days and the most common red flag."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM checks
                WHERE created_at > NOW() - INTERVAL '7 days' AND verdict <> 'low_risk'
                """
            )
            count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT flag, COUNT(*) AS n
                FROM checks, jsonb_array_elements_text(flags) AS flag
                WHERE created_at > NOW() - INTERVAL '7 days' AND verdict <> 'low_risk'
                GROUP BY flag ORDER BY n DESC, flag LIMIT 1
                """
            )
            row = cur.fetchone()
    finally:
        conn.close()
    return {"count": count, "top_flag": row[0] if row else None}


def mark_sent(ids):
    if not ids:
        return
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE alert_subscribers SET last_sent_at = NOW() WHERE id = ANY(%s)", (ids,))
        conn.commit()
    finally:
        conn.close()


# ---- messages ---------------------------------------------------------------

def alert_text(language, key):
    return ALERT_TEXT.get(language, ALERT_TEXT["en"])[key]


def weekly_message(language, summary):
    if not summary["count"] or not summary["top_flag"]:
        return alert_text(language, "quiet")
    return alert_text(language, "weekly").format(
        count=summary["count"], reason=messages.flag_label(language, summary["top_flag"])
    )


# ---- routes -----------------------------------------------------------------

@alerts_bp.route("/api/alerts/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "body must be a JSON object"}), 400
    phone = normalize_phone(data.get("phone"))
    language = data.get("language", "en")
    if phone is None:
        return jsonify({"error": "enter a valid Rwandan phone number"}), 400
    if language not in messages.LANGUAGES:
        return jsonify({"error": "language must be en or rw"}), 400
    if not subscribe_limiter.allow(phone):
        return jsonify({"error": "too many requests, try again later"}), 429

    try:
        save_subscriber(phone, language)
    except Exception:
        log.exception("Could not save alert subscriber")
        return jsonify({"error": "service unavailable"}), 503

    # The welcome text tells the owner of the number how to stop, in case
    # someone else typed it in.
    if is_configured():
        try:
            send_sms(phone, alert_text(language, "welcome"))
        except SmsError:
            log.exception("Could not send welcome SMS")
    return jsonify({"subscribed": True})


@alerts_bp.route("/api/alerts/unsubscribe", methods=["POST"])
def unsubscribe_route():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or normalize_phone(data.get("phone")) is None:
        return jsonify({"error": "enter a valid Rwandan phone number"}), 400
    try:
        unsubscribe(data["phone"])
    except Exception:
        log.exception("Could not unsubscribe")
        return jsonify({"error": "service unavailable"}), 503
    # Same answer whether or not the number was subscribed, so nobody can
    # use this to find out who gets alerts.
    return jsonify({"unsubscribed": True})


@alerts_bp.route("/api/alerts/send-weekly", methods=["POST"])
def send_weekly():
    expected = os.environ.get("ALERTS_CRON_TOKEN", "")
    given = request.headers.get("X-Cron-Token", "")
    if not expected or not hmac.compare_digest(given, expected):
        return jsonify({"error": "not allowed"}), 403
    if not is_configured():
        return jsonify({"error": "SMS is not configured"}), 503

    try:
        summary = weekly_summary()
        subscribers = active_subscribers()
    except Exception:
        log.exception("Could not load weekly alert data")
        return jsonify({"error": "service unavailable"}), 503

    sent, failed = [], 0
    for sub in subscribers:
        try:
            send_sms(sub["phone"], weekly_message(sub["language"], summary))
            sent.append(sub["id"])
        except SmsError:
            failed += 1
            log.warning("Weekly alert failed for subscriber %s", sub["id"])

    try:
        mark_sent(sent)
    except Exception:
        log.exception("Could not record sent alerts")
    return jsonify({"sent": len(sent), "failed": failed})
