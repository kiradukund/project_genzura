import re

_PATTERNS = [
    (r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
    (r"\+?[\d\s\-().]{7,15}", "[PHONE]"),
    (r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[NAME]"),
]


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text
