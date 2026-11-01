import re

# Rwandan unspaced numbers: 0788123456, 250788123456, +250788123456
_RW_PHONE_RE = re.compile(r"(?:\+?250|\b0)7[2389]\d{7}\b")

# Phone: must start with + or a digit followed by space/dash then more digits
# Requires at least one space OR a leading + to avoid matching dates (2026-11-03)
# e.g. +250 788 123 456, 0788 123 456 — but NOT 2026-11-03
_PHONE_RE = re.compile(r"(?:\+\d[\d\s\-]{6,14}\d|\b\d{3,5}[\s]\d{3}[\d\s]{0,8}\d)(?!\d)")

# Email
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Name: two capitalised words — NOTE: also masks proper nouns like "Western Union"
# Limitation accepted: narrowing further would risk missing real names.
_NAME_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")


def redact(text: str) -> str:
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _RW_PHONE_RE.sub("[PHONE]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _NAME_RE.sub("[NAME]", text)
    return text
