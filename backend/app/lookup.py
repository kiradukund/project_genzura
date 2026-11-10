# OWNER: Abay
"""Entity lookup.

Pulls phone numbers, emails and links out of a message, hashes them (keyed
HMAC, never stored in clear), counts how often they were reported, and adds a
flag to a /api/check result when a contact is already known.

Only reports create or bump rows in `entities`. Checks and lookups only read.
"""
import hashlib
import hmac
import logging
import os
import re
from urllib.parse import urlsplit

from psycopg2.extras import RealDictCursor

from .db import _get_conn
from .rules import add_flag

log = logging.getLogger(__name__)

# One report could be a mistake or a grudge: two or more make a contact "reported".
REPORTED_THRESHOLD = 2
BLACKLISTED_WEIGHT = 50
REPORTED_WEIGHT = 25
MAX_ENTITIES = 20  # per message, so one huge paste cannot flood the table

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+"
    r"|\b(?:bit\.ly|tinyurl\.com|t\.me|wa\.me|goo\.gl|cutt\.ly|rb\.gy|forms\.gle)/[^\s<>\"']+",
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"(?<!\w)(?:\+|00)?\d[\d\s\-()]{7,16}\d(?!\w)")


# ---------- normalizing ----------

def normalize_email(raw):
    return raw.strip().lower()


def normalize_link(raw):
    raw = raw.strip().rstrip(".,;:!?)]}'\"")
    if not re.match(r"^https?://", raw, re.IGNORECASE):
        raw = "http://" + raw
    try:
        parts = urlsplit(raw)
        host = (parts.hostname or "").lower()
    except ValueError:
        return None
    if host.startswith("www."):
        host = host[4:]
    if not host or "." not in host:
        return None
    query = f"?{parts.query}" if parts.query else ""
    return f"{host}{parts.path.rstrip('/')}{query}"


def normalize_phone(raw):
    """Return E.164 ("+250788123456") or None. Local Rwandan formats are accepted."""
    raw = raw.strip()
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+"):
        pass
    elif digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 10:
        digits = "250" + digits[1:]
    elif len(digits) == 9 and digits.startswith("7"):
        digits = "250" + digits
    if not 9 <= len(digits) <= 15:  # also drops 16-digit national IDs and dates
        return None
    return "+" + digits


# ---------- extracting ----------

def extract_entities(text):
    """Return [{"kind", "value"}] for emails, links and phones, deduplicated."""
    text = text or ""
    found, seen = [], set()

    def add(kind, value):
        if value and (kind, value) not in seen and len(found) < MAX_ENTITIES:
            seen.add((kind, value))
            found.append({"kind": kind, "value": value})

    for match in EMAIL_RE.findall(text):
        add("email", normalize_email(match))
    text = EMAIL_RE.sub(" ", text)  # digits inside an email are not a phone number

    for match in URL_RE.findall(text):
        add("link", normalize_link(match))
    text = URL_RE.sub(" ", text)

    for match in PHONE_RE.findall(text):
        add("phone", normalize_phone(match))

    return found


# ---------- hashing ----------

def _key():
    key = os.getenv("ENTITY_HASH_KEY")
    if not key:
        raise RuntimeError("ENTITY_HASH_KEY is not set")
    return key.encode()


def hash_value(kind, normalized):
    return hmac.new(_key(), f"{kind}:{normalized}".encode(), hashlib.sha256).hexdigest()


def hashed_entities(text):
    return [
        {**e, "value_hash": hash_value(e["kind"], e["value"])}
        for e in extract_entities(text)
    ]


# ---------- database ----------

def fetch_entities(pairs):
    """pairs: [(kind, value_hash)] -> matching rows."""
    if not pairs:
        return []
    conn = _get_conn()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT kind, value_hash, report_count, status
                   FROM entities WHERE (kind, value_hash) IN %s""",
                (tuple(pairs),),
            )
            return cur.fetchall()
    finally:
        conn.close()


def record_report(pairs):
    """Create each entity or add one to its report_count (one transaction)."""
    if not pairs:
        return
    conn = _get_conn()
    try:
        with conn, conn.cursor() as cur:
            for kind, value_hash in pairs:
                cur.execute(
                    """INSERT INTO entities (kind, value_hash, report_count)
                       VALUES (%s, %s, 1)
                       ON CONFLICT (kind, value_hash) DO UPDATE
                       SET report_count = entities.report_count + 1,
                           last_seen_at = NOW()""",
                    (kind, value_hash),
                )
    finally:
        conn.close()


# ---------- logic ----------

def assess(row):
    """Return (flag_id, weight) for one entity row, or None if it is not risky."""
    if row["status"] == "blacklisted":
        return ("blacklisted_contact", BLACKLISTED_WEIGHT)
    if row["status"] == "flagged" or row["report_count"] >= REPORTED_THRESHOLD:
        return ("reported_contact", REPORTED_WEIGHT)
    return None


def apply_entity_flags(result, text):
    """Add flags to a /api/check result for contacts that are already known."""
    entities = hashed_entities(text)
    if not entities:
        return result
    rows = fetch_entities([(e["kind"], e["value_hash"]) for e in entities])
    for row in rows:
        verdict = assess(row)
        if verdict:
            result = add_flag(result, *verdict)
    return result


def lookup(text):
    """For POST /api/lookup: what do we know about each contact in this message?"""
    entities = hashed_entities(text)
    rows = {}
    if entities:
        rows = {
            (r["kind"], r["value_hash"]): r
            for r in fetch_entities([(e["kind"], e["value_hash"]) for e in entities])
        }
    out = []
    for e in entities:
        row = rows.get((e["kind"], e["value_hash"]))
        out.append({
            "kind": e["kind"],
            "value": e["value"],
            "known": row is not None,
            "risky": bool(row and assess(row)),
            "report_count": row["report_count"] if row else 0,
            "status": row["status"] if row else "unknown",
        })
    return out


def record_report_entities(text):
    """Count a report against every contact in its description. Returns how many."""
    entities = hashed_entities(text)
    record_report([(e["kind"], e["value_hash"]) for e in entities])
    return len(entities)