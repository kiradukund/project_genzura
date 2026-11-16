# OWNER: Chol - Link checker: find suspicious URLs in a message
# (finished and connected to the score by Kevin, Nov 2026)
import re

SUSPICIOUS_LINK_FLAG = "suspicious_link"
SUSPICIOUS_LINK_WEIGHT = 20

# Endings that scam sites use a lot. Real organisations almost never do.
_SPAM_TLDS = (
    "xyz", "top", "click", "loan", "win", "gq", "cf", "tk", "ml", "ga",
    "buzz", "rest", "icu", "cfd", "sbs", "monster", "work", "live", "online", "site",
)
_COMMON_TLDS = ("com", "net", "org", "info", "biz", "co", "io", "me", "rw", "gov", "int", "edu", "ly", "gd", "at", "cc", "id")

_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "rb.gy", "cutt.ly",
    "short.io", "is.gd", "shorturl.at", "tiny.cc", "s.id",
}

# A link is: http(s)://..., www...., or a bare domain with a known ending
# ("visit canada-visa.xyz/apply", "bit.ly/abc"). Emails are skipped by the (?<!@) guard.
_URL_RE = re.compile(
    r"https?://[^\s<>\"')\]]+"
    r"|\bwww\.[^\s<>\"')\]]+"
    r"|(?<![@\w.-])(?:[a-z0-9-]+\.)+(?:" + "|".join(_SPAM_TLDS + _COMMON_TLDS) + r")\b(?:/[^\s<>\"')\]]*)?",
    re.IGNORECASE,
)
_RAW_IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

# Real government and international domains end like this. Anything else that calls
# itself "gov", "embassy" or "government" in its name is pretending.
_OFFICIAL_SUFFIXES = (
    ".gov.rw", ".gov", ".mil", ".gov.uk", ".gc.ca", ".canada.ca", ".gov.au", ".govt.nz",
    ".go.ke", ".go.ug", ".go.tz", ".gov.za", ".gov.ng", ".gov.gh", ".gov.bi",
    ".europa.eu", ".int", ".un.org",
)
_OFFICIAL_WORDS_RE = re.compile(r"(?:^|[.-])(gov|govt|government|embassy|official|ministry)(?:[.-]|$)")


def extract_urls(text):
    """All links in the text, in order, without trailing punctuation."""
    return [m.rstrip(".,;:!?") for m in _URL_RE.findall(text or "")]


def extract_domain(url):
    """'https://Bit.ly/x?y' -> 'bit.ly'. Returns '' when there is no host."""
    host = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    host = re.split(r"[/?#]", host, maxsplit=1)[0]
    host = host.split("@")[-1].split(":")[0]  # drop "user@" tricks and ports
    return host.lower().strip(".")


def _pretends_official(domain):
    if ("." + domain).endswith(_OFFICIAL_SUFFIXES):
        return False
    return bool(_OFFICIAL_WORDS_RE.search(domain))


def is_suspicious_url(url):
    domain = extract_domain(url)
    if not domain:
        return False
    return (
        domain in _SHORTENERS
        or domain.endswith(tuple("." + t for t in _SPAM_TLDS))
        or bool(_RAW_IP_RE.match(domain))
        or "xn--" in domain                      # look-alike letters (punycode)
        or _pretends_official(domain)
        or url.lower().startswith("http://")     # no encryption
    )


def find_suspicious_links(text: str) -> list[str]:
    """Return the suspicious URLs found in text (empty list = nothing suspicious).

    Offline only, no internet calls. Each entry is the URL as written in the text.
    """
    return [url for url in extract_urls(text) if is_suspicious_url(url)]


def link_flags(text):
    """Flags for the rule engine: [(flag_id, weight)]."""
    return [(SUSPICIOUS_LINK_FLAG, SUSPICIOUS_LINK_WEIGHT)] if find_suspicious_links(text) else []
