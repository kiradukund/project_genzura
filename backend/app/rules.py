def evaluate(text, context="job"):
    """Abay will implement the scam-detection rule engine here.

    Must return a dict with: risk_score (0-100), verdict
    (low_risk / suspicious / high_risk), flags (list of strings).
    """
    return {
        "risk_score": 0,
        "verdict": "low_risk",
        "flags": [],
        "message": "placeholder: rule engine not implemented yet",
    }
