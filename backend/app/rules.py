
import re

# Each rule: id, weight (points added to the risk score), regex pattern
RULES = [
    {
        "id": "upfront_fee",
        "weight": 40,
        "pattern": r"\b(registration|processing|application|visa|medical|training)\s+fee\b"
                   r"|western union|moneygram|\bmomo\b|mobile money",
    },
    {
        "id": "guaranteed_outcome",
        "weight": 20,
        "pattern": r"\bguaranteed\b|no interview|no experience needed|100% sure",
    },
    {
        "id": "urgency_pressure",
        "weight": 15,
        "pattern": r"\burgent(ly)?\b|act now|last chance|limited slots|within 24 hours",
    },
    {
        "id": "free_email_contact",
        "weight": 15,
        "pattern": r"@(gmail|yahoo|hotmail|outlook)\.com",
    },
    {
        "id": "chat_app_only",
        "weight": 10,
        "pattern": r"\b(whatsapp|telegram)\b",
    },
    {
        "id": "sensitive_info_request",
        "weight": 25,
        "pattern": r"\b(send|share|give)\b.*\b(passport|bank account|pin|password|otp)\b",
    },
]


def evaluate(text, context="job"):
    """Score a message. Returns {"risk_score", "verdict", "flags"}."""
    text = text or ""
    flags = []
    score = 0

    for rule in RULES:
        if re.search(rule["pattern"], text, re.IGNORECASE):
            flags.append(rule["id"])
            score += rule["weight"]

    score = min(score, 100)

    if score >= 60:
        verdict = "high_risk"
    elif score >= 30:
        verdict = "suspicious"
    else:
        verdict = "low_risk"

    return {"risk_score": score, "verdict": verdict, "flags": flags}