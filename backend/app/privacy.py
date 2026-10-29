# Privacy and data-masking helpers go here
"""Privacy and data-masking helpers.

Only masked text is ever stored in the database. Phone numbers of USSD/SMS
senders are never persisted.
"""
import re

# Order matters: longest/most specific patterns first.
_PATTERNS = [
    ("[ID]", re.compile(r"(?<!\d)\d{16}(?!\d)")),               # Rwanda national ID
    ("[EMAIL]", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("[PHONE]", re.compile(r"(?<!\w)(?:\+|00)?\d[\d\s\-()]{7,16}\d(?!\w)")),
]


def mask_text(text):
    """Replace IDs, emails and phone numbers with placeholders."""
    masked = text or ""
    for placeholder, pattern in _PATTERNS:
        masked = pattern.sub(placeholder, masked)
    return masked