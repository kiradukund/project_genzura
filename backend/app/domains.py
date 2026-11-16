# OWNER: Kevin - Domain trust: look-alike sites, hidden redirects, brand-new domains
"""Checks the websites and email domains in a message.

Offline (fast, used by every channel through rules.evaluate):
    impersonates_official_site  a domain that copies an official organisation's name
                                (irembo-gov.com, mifotra-jobs.rw, rlb.gov.rw ...)

Online (web and WhatsApp checks only, through routes._evaluate):
    hidden_redirect   a short link that leads to a suspicious website
    new_domain        the website was registered less than NEW_DOMAIN_DAYS ago

Online checks have a hard time budget, never call private network addresses
(SSRF protection), cache their answers and fail silently: if the internet is slow,
the message is still scored with the offline rules.
"""
import ipaddress
import logging
import os
import re
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests

from .links import extract_domain, extract_urls, is_suspicious_url

log = logging.getLogger(__name__)

IMPERSONATION_FLAG, IMPERSONATION_WEIGHT = "impersonates_official_site", 35
REDIRECT_FLAG, REDIRECT_WEIGHT = "hidden_redirect", 20
NEW_DOMAIN_FLAG, NEW_DOMAIN_WEIGHT = "new_domain", 20

NEW_DOMAIN_DAYS = 90
MAX_LINKS = 3            # online checks per message
MAX_REDIRECTS = 5
REQUEST_TIMEOUT = 2.5    # seconds per network call
TOTAL_BUDGET = 4.0       # seconds for all online checks of one message
CACHE_TTL = 24 * 3600
CACHE_MAX = 2000

# Official organisations Genzura users are most often lured with: their real domain and
# the name scammers copy. Rwandan entries match the Official Verification Directory.
OFFICIAL_SITES = {
    "irembo.gov.rw": "irembo",
    "rib.gov.rw": "rib",
    "migration.gov.rw": "migration",
    "minaffet.gov.rw": "minaffet",
    "mifotra.gov.rw": "mifotra",
    "mineduc.gov.rw": "mineduc",
    "hec.gov.rw": "hec",
    "rtb.gov.rw": "rtb",
    "minijust.gov.rw": "minijust",
    "police.gov.rw": "police",
    "rra.gov.rw": "rra",
    "rdb.rw": "rdb",
    "bnr.rw": "bnr",
    "rssb.rw": "rssb",
    "rura.rw": "rura",
    "mtn.co.rw": "mtn",
    "airtel.co.rw": "airtel",
    "rwanda.iom.int": "iom",
    "iom.int": "iom",
    "unicef.org": "unicef",
    "unhcr.org": "unhcr",
    "canada.ca": "canada",
    "usembassy.gov": "usembassy",
}
# Real sites of the same organisations that are not in the list above.
OTHER_REAL_DOMAINS = {"mtn.com", "mtngroup.com", "airtel.com", "airtel.africa", "airtel.in", "iom.int"}
# Everyday words: only suspicious next to "gov" or "rwanda" (migration-gov.rw, police-rwanda.com).
GENERIC_NAMES = {"migration", "police", "canada"}
_GOVERNMENT_HINTS = {"gov", "govt", "government", "rw", "rwanda", "official", "visa", "embassy", "ministry"}
# Short names like "rib" or "hec" appear inside normal words, so they only count as a
# whole label part ("rib-rwanda.com"), never inside another word ("caribbean.com").
_MIN_FREE_MATCH = 5

# Two-part endings, so "irembo.gov.rw" -> registrable "irembo.gov.rw", not "gov.rw".
_TWO_PART_SUFFIXES = {
    "gov.rw", "co.rw", "ac.rw", "org.rw", "net.rw", "co.uk", "gov.uk", "ac.uk", "org.uk",
    "co.ke", "go.ke", "or.ke", "co.ug", "go.ug", "co.tz", "go.tz", "co.za", "gov.za",
    "com.ng", "gov.ng", "com.gh", "gov.gh", "com.au", "gov.au", "gc.ca", "co.in",
}

_ONLINE_ENABLED = os.getenv("DOMAIN_CHECKS_ONLINE", "true").lower() != "false"
_USER_AGENT = "GenzuraLinkCheck/1.0 (+https://genzura-web.onrender.com)"


# ---------- helpers ----------

def registrable_domain(domain):
    """'apply.irembo-gov.com' -> 'irembo-gov.com', 'www.irembo.gov.rw' -> 'irembo.gov.rw'."""
    parts = domain.lower().strip(".").split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in _TWO_PART_SUFFIXES:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _domains_in(text):
    """Domains from the links and email addresses in a message."""
    found = [extract_domain(u) for u in extract_urls(text)]
    found += [m.lower() for m in re.findall(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)", text or "")]
    seen, out = set(), []
    for d in found:
        if d and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def _is_official(domain):
    real_sites = list(OFFICIAL_SITES) + list(OTHER_REAL_DOMAINS)
    return any(domain == real or domain.endswith("." + real) for real in real_sites)


def _one_letter_off(a, b):
    """True when a and b differ by exactly one letter swap, insertion or deletion."""
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        diffs = [i for i in range(len(a)) if a[i] != b[i]]
        if len(diffs) == 1:
            return True
        return len(diffs) == 2 and diffs[1] == diffs[0] + 1 and a[diffs[0]] == b[diffs[1]] and a[diffs[1]] == b[diffs[0]]
    short, long_ = (a, b) if len(a) < len(b) else (b, a)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def impersonated_name(domain):
    """The official name a domain copies, or None. Real official domains return None."""
    domain = domain.lower()
    if _is_official(domain):
        return None
    registrable = registrable_domain(domain)
    labels = re.split(r"[.-]", domain)
    looks_governmental = bool(_GOVERNMENT_HINTS & set(labels))
    for real, name in OFFICIAL_SITES.items():
        if name in GENERIC_NAMES and not looks_governmental:
            continue
        real_registrable = registrable_domain(real)
        # copies the name as its own word: irembo-gov.com, rib-rwanda.org, mifotra.jobs.xyz
        if name in labels:
            return name
        # copies the name inside a longer word: iremboservices.com (long names only)
        if len(name) >= _MIN_FREE_MATCH and name in domain:
            return name
        # one letter off the real domain: mifotr.gov.rw, lrembo.gov.rw (names of 4+ letters)
        first = real_registrable.split(".")[0]
        if len(first) >= 4 and registrable.split(".")[1:] == real_registrable.split(".")[1:]:
            if _one_letter_off(registrable.split(".")[0], first):
                return name
    return None


def offline_flags(text):
    """Flags for the rule engine: [(flag_id, weight)]. No network."""
    if any(impersonated_name(d) for d in _domains_in(text)):
        return [(IMPERSONATION_FLAG, IMPERSONATION_WEIGHT)]
    return []


# ---------- online: safety ----------

def _public_host(host):
    """True only when every address the host resolves to is public (blocks SSRF)."""
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, OSError):
        return False
    if not infos:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global or ip.is_multicast:
            return False
    return True


# ---------- online: cache ----------

_cache, _cache_lock = {}, threading.Lock()


def _cached(key, compute):
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    value = compute()
    with _cache_lock:
        if len(_cache) >= CACHE_MAX:
            _cache.clear()
        _cache[key] = (now, value)
    return value


# ---------- online: checks ----------

def final_destination(url):
    """Follow redirects (HEAD only, no page bodies) and return the last URL, or None."""
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    for _ in range(MAX_REDIRECTS + 1):
        host = extract_domain(url)
        if not host or not _public_host(host):
            return None
        try:
            resp = requests.head(url, allow_redirects=False, timeout=REQUEST_TIMEOUT,
                                 headers={"User-Agent": _USER_AGENT})
        except requests.RequestException:
            return None
        location = resp.headers.get("Location")
        if resp.status_code in (301, 302, 303, 307, 308) and location:
            url = urljoin(url, location)
            if not re.match(r"^https?://", url, re.IGNORECASE):
                return None
            continue
        return url
    return None


def domain_age_days(domain):
    """Days since the domain was registered (public RDAP records), or None if unknown."""
    try:
        resp = requests.get(f"https://rdap.org/domain/{registrable_domain(domain)}",
                            timeout=REQUEST_TIMEOUT, headers={"User-Agent": _USER_AGENT})
        if resp.status_code != 200:
            return None
        for event in resp.json().get("events", []):
            if event.get("eventAction") == "registration":
                registered = datetime.fromisoformat(event["eventDate"].replace("Z", "+00:00"))
                return (datetime.now(timezone.utc) - registered).days
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None
    return None


def _check_link(url):
    """Flags for one link: [(flag_id, weight)]."""
    flags = []
    domain = extract_domain(url)
    destination = _cached(("dest", url), lambda: final_destination(url))
    if destination:
        final = extract_domain(destination)
        if final and final != domain and (is_suspicious_url(destination) or impersonated_name(final)):
            flags.append((REDIRECT_FLAG, REDIRECT_WEIGHT))
        domain = final or domain
    if domain and not _is_official(domain):
        age = _cached(("age", registrable_domain(domain)), lambda: domain_age_days(domain))
        if age is not None and age < NEW_DOMAIN_DAYS:
            flags.append((NEW_DOMAIN_FLAG, NEW_DOMAIN_WEIGHT))
    return flags


_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="domains")


def online_flags(text):
    """Network checks for up to MAX_LINKS links, within TOTAL_BUDGET seconds."""
    if not _ONLINE_ENABLED:
        return []
    urls = extract_urls(text)[:MAX_LINKS]
    if not urls:
        return []
    futures = [_pool.submit(_check_link, u) for u in urls]
    done, _ = wait(futures, timeout=TOTAL_BUDGET)
    flags = []
    for future in done:
        try:
            for flag in future.result():
                if flag not in flags:
                    flags.append(flag)
        except Exception:
            log.exception("Link check failed")
    return flags
