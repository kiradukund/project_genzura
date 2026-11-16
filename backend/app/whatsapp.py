"""WhatsApp bot (Meta WhatsApp Cloud API).

GET  /api/whatsapp  Meta's one-time webhook check (hub.challenge).
POST /api/whatsapp  Incoming messages: check the signature, score the text with
                    the same rules as the website, save a masked check with
                    channel 'whatsapp', and reply.

Privacy: the sender's number is used only to send the reply. It is never stored
or logged. Only redacted text is saved (via routes._save_check).

Secrets (Render environment, never in the repo):
    WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN,
    WHATSAPP_APP_SECRET, optional WHATSAPP_API_VERSION (default v24.0)
"""
import hashlib
import hmac
import json
import logging
import os
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify, request

from . import messages
from .lookup import MAX_TEXT_LENGTH
from .routes import _evaluate, _save_check

whatsapp_bp = Blueprint("whatsapp", __name__)

# OWNER: Didier - WhatsApp bot. Build: POST /api/whatsapp

log = logging.getLogger(__name__)

DIRECTORY_URL = "https://genzura-web.onrender.com/directory"


def _env(name, default=""):
    return os.environ.get(name, default)


# ---------- 1. Meta's one-time webhook check ----------

@whatsapp_bp.get("/api/whatsapp")
def verify_webhook():
    verify_token = _env("WHATSAPP_VERIFY_TOKEN")
    if (
        verify_token
        and request.args.get("hub.mode") == "subscribe"
        and hmac.compare_digest(request.args.get("hub.verify_token", ""), verify_token)
    ):
        return request.args.get("hub.challenge", ""), 200
    return "Forbidden", 403


# ---------- 2. Signature check ----------

def valid_signature(raw_body, header):
    """True if X-Hub-Signature-256 matches the body, signed with the app secret."""
    secret = _env("WHATSAPP_APP_SECRET")
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(header[len("sha256="):], expected)


# ---------- 3. Reading Meta's message format ----------

def incoming_texts(payload):
    """Yield (sender, text) for each text message. Status updates are skipped."""
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for msg in value.get("messages") or []:
                if msg.get("type") == "text":
                    body = (msg.get("text") or {}).get("body", "")
                    if msg.get("from") and body.strip():
                        yield msg["from"], body


# ---------- 4. Building the reply (texts come from Alier's messages.py) ----------

def build_reply(result, language="en"):
    lines = [messages.sms_result(language, result)]
    if result["flags"]:
        lines.append("")
        lines += [f"- {messages.flag_label(language, f)}" for f in result["flags"]]
    lines += ["", DIRECTORY_URL, "RIB: 166"]
    return "\n".join(lines)


# ---------- 5. Sending the reply ----------

def send_text(to, body):
    token = _env("WHATSAPP_TOKEN")
    phone_id = _env("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_id:
        log.warning("WhatsApp is not configured; reply not sent")
        return False
    version = _env("WHATSAPP_API_VERSION", "v24.0")
    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    data = json.dumps({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }).encode()
    req = Request(url, data=data, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        with urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except Exception:
        log.exception("WhatsApp send failed")  # no phone number in the log
        return False


# ---------- 6. The webhook ----------

@whatsapp_bp.post("/api/whatsapp")
def receive():
    raw = request.get_data()
    if not valid_signature(raw, request.headers.get("X-Hub-Signature-256", "")):
        return jsonify({"error": "invalid signature"}), 403
    try:
        payload = json.loads(raw or b"{}")
    except ValueError:
        return jsonify({"status": "ignored"}), 200

    for sender, text in incoming_texts(payload):
        text = text[:MAX_TEXT_LENGTH]
        result = _evaluate(text, "job")
        _save_check("whatsapp", "job", "en", text, result)
        send_text(sender, build_reply(result))

    # Always 200 for valid requests, so Meta does not keep retrying.
    return jsonify({"status": "ok"}), 200
