# OWNER: Kuol - SMS via Africa's Talking. POST /api/send-result and inbound SMS
"""SMS for Genzura.

POST /api/send-result   {"phone", "check_id", "language"}
    Website button "Send result to my phone": texts the result of a recent check.

POST /api/sms/inbound   (Africa's Talking incoming-SMS callback, form fields from, text...)
    Someone texts an offer to our short code; we check it and text back the result.
    Start the text with "RW" for a Kinyarwanda reply. "STOP" ends scam alerts.

Settings (backend/.env, never commit real keys):
    AT_USERNAME   "sandbox" while testing in the Africa's Talking simulator
    AT_API_KEY    API key from the Africa's Talking dashboard
    AT_SENDER_ID  optional short code or sender name

Phone numbers are never saved by this file.
"""
import logging
import os
import re
import threading
import time

import requests
from flask import Blueprint, jsonify, request

from . import messages
from .db import _get_conn, save_check
from .privacy import redact
from .rules import evaluate

log = logging.getLogger(__name__)
sms_bp = Blueprint("sms", __name__)

LIVE_URL = "https://api.africastalking.com/version1/messaging"
SANDBOX_URL = "https://api.sandbox.africastalking.com/version1/messaging"

# Rwandan mobile: 07X XXX XXXX, 2507X XXX XXXX or +2507X XXX XXXX
RW_PHONE = re.compile(r"^(?:\+?250|0)(7[2389]\d{7})$")

# Limits so the button cannot be used to spam a number (SMS costs money).
MAX_SENDS_PER_PHONE = 3
WINDOW_SECONDS = 15 * 60
CHECK_MAX_AGE_HOURS = 24
MAX_INBOUND_LENGTH = 2000


class SmsError(Exception):
    pass


def normalize_phone(phone):
    """'0788 123 456' -> '+250788123456', or None if it is not a Rwandan mobile number."""
    if not isinstance(phone, str):
        return None
    match = RW_PHONE.match(re.sub(r"[\s\-()]", "", phone))
    return f"+250{match.group(1)}" if match else None


def is_configured():
    return bool(os.environ.get("AT_USERNAME") and os.environ.get("AT_API_KEY"))


def send_sms(phone, message):
    """Send one SMS through Africa's Talking. Raises SmsError if it was not accepted."""
    username = os.environ.get("AT_USERNAME", "")
    api_key = os.environ.get("AT_API_KEY", "")
    if not (username and api_key):
        raise SmsError("SMS is not configured")

    data = {"username": username, "to": phone, "message": message}
    sender = os.environ.get("AT_SENDER_ID")
    if sender:
        data["from"] = sender

    url = SANDBOX_URL if username == "sandbox" else LIVE_URL
    try:
        res = requests.post(
            url,
            data=data,
            headers={"apiKey": api_key, "Accept": "application/json"},
            timeout=10,
        )
        res.raise_for_status()
        recipients = res.json()["SMSMessageData"]["Recipients"]
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise SmsError("SMS provider error") from exc

    if not recipients or recipients[0].get("status") != "Success":
        raise SmsError("SMS was not accepted")


class RateLimiter:
    """Counts sends per phone in memory (resets when the server restarts)."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.sent = {}
        self.lock = threading.Lock()

    def allow(self, key):
        now = time.monotonic()
        with self.lock:
            recent = [t for t in self.sent.get(key, []) if now - t < self.window]
            if len(recent) >= self.limit:
                self.sent[key] = recent
                return False
            self.sent[key] = recent + [now]
            return True


limiter = RateLimiter(MAX_SENDS_PER_PHONE, WINDOW_SECONDS)


def get_check(check_id):
    """Verdict and flags of a check saved in the last 24 hours, or None."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT verdict, flags, risk_score FROM checks
                WHERE id = %s AND created_at > NOW() - make_interval(hours => %s)
                """,
                (check_id, CHECK_MAX_AGE_HOURS),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {"verdict": row[0], "flags": row[1] or [], "risk_score": row[2]}


@sms_bp.route("/api/send-result", methods=["POST"])
def send_result():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "body must be a JSON object"}), 400

    phone = normalize_phone(data.get("phone"))
    check_id = data.get("check_id")
    language = data.get("language", "en")

    if phone is None:
        return jsonify({"error": "enter a valid Rwandan phone number"}), 400
    if not isinstance(check_id, int) or isinstance(check_id, bool) or check_id <= 0:
        return jsonify({"error": "check_id is required"}), 400
    if language not in messages.LANGUAGES:
        return jsonify({"error": "language must be en or rw"}), 400
    if not is_configured():
        return jsonify({"error": "SMS is not available yet"}), 503

    try:
        result = get_check(check_id)
    except Exception:
        log.exception("Could not load check for SMS")
        return jsonify({"error": "service unavailable"}), 503
    if result is None:
        return jsonify({"error": "check not found"}), 404

    if not limiter.allow(phone):
        return jsonify({"error": "too many messages to this number, try again later"}), 429

    try:
        send_sms(phone, messages.sms_result(language, result))
    except SmsError:
        log.exception("Could not send result SMS")
        return jsonify({"error": "could not send the SMS"}), 502

    return jsonify({"sent": True})


def parse_inbound(text):
    """'RW <offer>' -> ('rw', '<offer>'); anything else is English."""
    text = (text or "").strip()
    match = re.match(r"^rw\b[\s:,.-]*", text, re.IGNORECASE)
    if match:
        return "rw", text[match.end():].strip()
    return "en", text


@sms_bp.route("/api/sms/inbound", methods=["POST"])
def inbound():
    """Africa's Talking incoming SMS. We always answer 200 so it does not retry."""
    sender = request.form.get("from", "")
    phone = normalize_phone(sender) or (sender if sender.startswith("+") else None)
    raw = (request.form.get("text") or "")[:MAX_INBOUND_LENGTH]

    if raw.strip().upper() in {"STOP", "HAGARIKA"}:
        from .alerts import unsubscribe  # imported here: alerts.py also imports this file

        try:
            unsubscribe(sender)
        except Exception:
            log.exception("Could not unsubscribe by SMS")
        return "", 200

    language, offer = parse_inbound(raw)
    if not offer or phone is None:
        return "", 200

    result = evaluate(offer, "job")
    try:
        save_check(redact(offer), "job", result["risk_score"],
                   result["verdict"], result["flags"], "sms", language)
    except Exception:
        log.exception("Could not save SMS check")

    if limiter.allow(phone):
        try:
            send_sms(phone, messages.sms_result(language, result))
        except SmsError:
            log.exception("Could not send SMS reply")
    return "", 200
