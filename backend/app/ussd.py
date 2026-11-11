# OWNER: Kuol - USSD via Africa's Talking. POST /api/ussd
"""USSD menu for feature phones.

Africa's Talking calls this URL on every screen of a session with form fields:
sessionId, serviceCode, phoneNumber, text. `text` holds everything the user has
typed so far, joined with "*" (e.g. "1*2*Pay the visa fee"). We reply in plain
text: "CON ..." shows a screen and waits for input, "END ..." closes the session.

Flow:
    ""                 -> choose language        (CON)
    "1"                -> choose offer type      (CON)
    "1*3"              -> type the message       (CON)
    "1*3*<message>"    -> risk result            (END)

The phone number is never stored. Only the masked message is saved, like the website.
"""
import logging

from flask import Blueprint, Response, request

from . import messages
from .db import save_check
from .privacy import redact
from .rules import evaluate

log = logging.getLogger(__name__)
ussd_bp = Blueprint("ussd", __name__)

CONTEXT_CHOICES = {"1": "job", "2": "scholarship", "3": "visa"}


def con(body):
    return Response(f"CON {body}", mimetype="text/plain")


def end(body):
    return Response(f"END {body}", mimetype="text/plain")


def menu_reply(text):
    """Work out the next screen from everything typed so far."""
    if not text:
        return con(messages.LANGUAGE_MENU)

    # The message itself may contain "*", so only split off the first two answers.
    parts = text.split("*", 2)
    language = messages.LANGUAGE_CHOICES.get(parts[0].strip())
    if language is None:
        return end(messages.text("en", "invalid"))
    if len(parts) == 1:
        return con(messages.text(language, "main_menu"))

    context = CONTEXT_CHOICES.get(parts[1].strip())
    if context is None:
        return end(messages.text(language, "invalid"))
    if len(parts) == 2:
        return con(messages.text(language, "ask_message"))

    offer = parts[2].strip()
    if not offer:
        return end(messages.text(language, "invalid"))

    result = evaluate(offer, context)
    try:
        save_check(redact(offer), context, result["risk_score"],
                   result["verdict"], result["flags"], "ussd", language)
    except Exception:
        log.exception("Could not save USSD check")
    return end(messages.ussd_result(language, result))


@ussd_bp.route("/api/ussd", methods=["POST"])
def ussd():
    return menu_reply((request.form.get("text") or "").strip())
