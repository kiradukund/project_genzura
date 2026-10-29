# Third-party integrations (e.g. Africa's Talking) go here
"""Third-party integrations (Africa's Talking: SMS + USSD)."""
import logging
import os

import requests

log = logging.getLogger(__name__)

AT_SMS_URL = "https://api.africastalking.com/version1/messaging"
AT_SANDBOX_SMS_URL = "https://api.sandbox.africastalking.com/version1/messaging"


def send_sms(to, message):
    """Send an SMS through Africa's Talking. Returns True on success."""
    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    if not username or not api_key:
        log.warning("Africa's Talking credentials missing; SMS not sent")
        return False

    url = AT_SANDBOX_SMS_URL if username == "sandbox" else AT_SMS_URL
    try:
        resp = requests.post(
            url,
            headers={"apiKey": api_key, "Accept": "application/json"},
            data={"username": username, "to": to, "message": message},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException:
        log.exception("Failed to send SMS")
        return False


def ussd_continue(text):
    """USSD reply that keeps the session open."""
    return f"CON {text}"


def ussd_end(text):
    """USSD reply that closes the session."""
    return f"END {text}"