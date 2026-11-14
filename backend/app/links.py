# OWNER: Chol - Link checker: find suspicious URLs in a message
import re

_URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)

_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "rb.gy", "cutt.ly", "short.io"}
_SPAM_TLDS = {".xyz", ".top", ".click", ".loan", ".win", ".gq", ".cf", ".tk", ".ml"}
_RAW_IP_RE = re.compile(r"https?://\d{1,3}(?:\.\d{1,3}){3}")
_LOOKALIKE_RE = re.compile(r"xn--")
# Matches fake gov/embassy domains but NOT real ones like gov.rw, gov.uk
_FAKE_GOV_RE = re.compile(
    r"(?<!\.)(?:embassy|government|official)[.\-](?!gov\b)"
    r"|(?:^|\.)gov[.\-](?!rw|uk|au|us|ca|za|ke|ug|tz|et|gh|ng|cm|sn|ci|bj|tg|bf|ml|ne|td|sd|so|dj|er|mw|zm|zw|mz|mg|mu|sc|km|cv|st|gw|sl|lr|gm|gn|mr|eh)",
    re.IGNORECASE,
)


def _extract_domain(url: str) -> str:
    url = re.sub(r"https?://", "", url, flags=re.IGNORECASE)
    return url.split("/")[0].lower()


def find_suspicious_links(text: str) -> list[str]:
    """Return a list of suspicious URLs found in text. Offline only, no internet calls.

    Abay: call this from the rule engine. Returns a list of suspicious URL strings
    (empty list = nothing suspicious). Each entry is the original URL from the text.
    """
    urls = _URL_RE.findall(text or "")
    suspicious = []
    for url in urls:
        domain = _extract_domain(url)
        if (
            domain in _SHORTENERS
            or any(domain.endswith(tld) for tld in _SPAM_TLDS)
            or _RAW_IP_RE.match(url)
            or _LOOKALIKE_RE.search(domain)
            or _FAKE_GOV_RE.search(domain)
            or url.startswith("http://")
        ):
            suspicious.append(url)
    return suspicious
