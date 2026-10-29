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
        # [\s\S] so the match also works across line breaks
        "pattern": r"\b(send|share|give)\b[\s\S]{0,80}\b(passport|bank account|pin|password|otp)\b",
    },
    # ---- Kinyarwanda (DRAFT: have a native speaker review these) ----
    {
        "id": "upfront_fee",
        "weight": 40,
        "pattern": r"amafaranga\s+yo\s+kwiyandikisha|amafaranga\s+y['’]?(ibyangombwa|viza)"
                   r"|(kwishyura|kohereza|ohereza)\s+amafaranga",
    },
    {
        "id": "guaranteed_outcome",
        "weight": 20,
        "pattern": r"nta\s+kizamini|nta\s+bunararibonye|wizeye\s+ko\s+uzabona",
    },
    {
        "id": "urgency_pressure",
        "weight": 15,
        "pattern": r"byihutirwa|ako\s+kanya|uyu\s+munsi\s+gusa|amasaha\s+24",
    },
    {
        "id": "sensitive_info_request",
        "weight": 25,
        "pattern": r"\b(ohereza|kohereza|tanga)\b[\s\S]{0,80}(pasiporo|konti\s+ya\s+banki|ijambo\s+ry['’]ibanga|\bpin\b|\botp\b)",
    },
]


def verdict_for(score):
    if score >= 60:
        return "high_risk"
    if score >= 30:
        return "suspicious"
    return "low_risk"


def evaluate(text, context="job"):
    """Score a message. Returns {"risk_score", "verdict", "flags"}."""
    text = text or ""
    flags = []
    score = 0

    for rule in RULES:
        # A flag counts once, even if both the English and Kinyarwanda rule match
        if rule["id"] in flags:
            continue
        if re.search(rule["pattern"], text, re.IGNORECASE):
            flags.append(rule["id"])
            score += rule["weight"]

    score = min(score, 100)
    return {"risk_score": score, "verdict": verdict_for(score), "flags": flags}


def add_flag(result, flag_id, weight):
    """Return a new result with an extra flag applied (once) and the verdict recomputed."""
    if flag_id in result["flags"]:
        return result
    score = min(result["risk_score"] + weight, 100)
    return {
        "risk_score": score,
        "verdict": verdict_for(score),
        "flags": result["flags"] + [flag_id],
    }