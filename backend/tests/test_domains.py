# OWNER: Kevin
import socket
from datetime import datetime, timedelta, timezone

import pytest

from app import create_app, domains, routes
from app.domains import (
    impersonated_name, offline_flags, online_flags, registrable_domain,
)
from app.rules import evaluate


# ---------- offline: look-alike names ----------

@pytest.mark.parametrize("domain, name", [
    ("irembo-gov.com", "irembo"),
    ("apply.irembo-services.rw", "irembo"),
    ("iremboservices.com", "irembo"),
    ("mifotra-recruitment.com", "mifotra"),
    ("mifotr.gov.rw", "mifotra"),          # one letter missing
    ("unicef-jobs.org", "unicef"),
    ("migration-gov.rw", "migration"),
    ("rib-rwanda.org", "rib"),
])
def test_copies_of_official_names_are_caught(domain, name):
    assert impersonated_name(domain) == name


@pytest.mark.parametrize("domain", [
    "irembo.gov.rw", "support.irembo.gov.rw", "www.unicef.org", "mtn.co.rw", "mtn.com",
    "rab.gov.rw",              # a real ministry agency one letter from "rib": short names are not compared
    "caribbean-jobs.com",      # "rib" inside another word
    "migration-help.com",      # everyday word with nothing official around it
    "rw.usembassy.gov",
])
def test_real_or_unrelated_domains_are_not_flagged(domain):
    assert impersonated_name(domain) is None


def test_registrable_domain_handles_two_part_endings():
    assert registrable_domain("www.irembo.gov.rw") == "irembo.gov.rw"
    assert registrable_domain("apply.irembo-gov.com") == "irembo-gov.com"
    assert registrable_domain("jobs.mtn.co.rw") == "mtn.co.rw"


def test_email_domains_are_checked_too():
    assert offline_flags("Send your CV to hr@mifotra-recruitment.com") == [("impersonates_official_site", 35)]
    assert offline_flags("Write to info@mifotra.gov.rw") == []


def test_impersonation_is_part_of_every_score():
    result = evaluate("Pay the visa fee at irembo-gov.com")
    assert "impersonates_official_site" in result["flags"]
    assert result["verdict"] == "high_risk"


# ---------- online: safety ----------

@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "::1"])
def test_private_addresses_are_never_called(monkeypatch, ip):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    monkeypatch.setattr(domains.socket, "getaddrinfo", lambda *a, **k: [(family, 1, 6, "", (ip, 0))])
    called = []
    monkeypatch.setattr(domains.requests, "head", lambda *a, **k: called.append(a))
    assert domains.final_destination("https://evil.example/x") is None
    assert called == []


def _public_dns(monkeypatch):
    monkeypatch.setattr(domains.socket, "getaddrinfo",
                        lambda *a, **k: [(socket.AF_INET, 1, 6, "", ("93.184.216.34", 0))])


class FakeResponse:
    def __init__(self, status=200, location=None, body=None):
        self.status_code = status
        self.headers = {"Location": location} if location else {}
        self._body = body or {}

    def json(self):
        return self._body


# ---------- online: redirects and domain age ----------

def test_short_link_is_followed_to_its_destination(monkeypatch):
    _public_dns(monkeypatch)
    hops = {"https://bit.ly/abc": FakeResponse(301, "https://irembo-gov.com/pay"),
            "https://irembo-gov.com/pay": FakeResponse(200)}
    monkeypatch.setattr(domains.requests, "head", lambda url, **k: hops[url])
    assert domains.final_destination("bit.ly/abc") == "https://irembo-gov.com/pay"


def test_redirect_loops_stop(monkeypatch):
    _public_dns(monkeypatch)
    monkeypatch.setattr(domains.requests, "head", lambda url, **k: FakeResponse(302, url))
    assert domains.final_destination("https://loop.example") is None


def test_redirect_to_a_non_web_address_is_refused(monkeypatch):
    _public_dns(monkeypatch)
    monkeypatch.setattr(domains.requests, "head", lambda url, **k: FakeResponse(302, "file:///etc/passwd"))
    assert domains.final_destination("https://evil.example") is None


def _rdap(days_ago):
    date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return FakeResponse(200, body={"events": [{"eventAction": "registration", "eventDate": date}]})


def test_domain_age_from_rdap(monkeypatch):
    monkeypatch.setattr(domains.requests, "get", lambda url, **k: _rdap(10))
    assert domains.domain_age_days("apply.new-jobs.com") == 10


def test_unknown_domain_age_is_none(monkeypatch):
    monkeypatch.setattr(domains.requests, "get", lambda url, **k: FakeResponse(404))
    assert domains.domain_age_days("something.rw") is None


@pytest.fixture
def fresh_cache(monkeypatch):
    monkeypatch.setattr(domains, "_cache", {})
    monkeypatch.setattr(domains, "_ONLINE_ENABLED", True)


def test_online_flags_for_a_new_site_behind_a_short_link(monkeypatch, fresh_cache):
    _public_dns(monkeypatch)
    hops = {"https://bit.ly/abc": FakeResponse(301, "https://canada-visa.xyz/pay"),
            "https://canada-visa.xyz/pay": FakeResponse(200)}
    monkeypatch.setattr(domains.requests, "head", lambda url, **k: hops[url])
    monkeypatch.setattr(domains.requests, "get", lambda url, **k: _rdap(12))
    assert online_flags("Pay here bit.ly/abc") == [("hidden_redirect", 20), ("new_domain", 20)]


def test_old_site_and_official_site_get_no_online_flags(monkeypatch, fresh_cache):
    _public_dns(monkeypatch)
    monkeypatch.setattr(domains.requests, "head", lambda url, **k: FakeResponse(200))
    monkeypatch.setattr(domains.requests, "get", lambda url, **k: _rdap(3000))
    assert online_flags("See https://www.unicef.org and https://jobs.example.com") == []


def test_answers_are_cached(monkeypatch, fresh_cache):
    _public_dns(monkeypatch)
    calls = []
    monkeypatch.setattr(domains.requests, "head", lambda url, **k: calls.append(url) or FakeResponse(200))
    monkeypatch.setattr(domains.requests, "get", lambda url, **k: _rdap(3000))
    online_flags("https://jobs.example.com")
    online_flags("https://jobs.example.com")
    assert len(calls) == 1


def test_slow_internet_never_blocks_the_answer(monkeypatch, fresh_cache):
    import time
    monkeypatch.setattr(domains, "TOTAL_BUDGET", 0.2)
    monkeypatch.setattr(domains, "_check_link", lambda url: time.sleep(2) or [("new_domain", 20)])
    start = time.monotonic()
    assert online_flags("https://slow.example.com") == []
    assert time.monotonic() - start < 1


def test_online_checks_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(domains, "_ONLINE_ENABLED", False)
    assert online_flags("bit.ly/abc") == []


# ---------- through the API ----------

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(routes, "_save_check", lambda *a, **k: None)
    monkeypatch.setattr(routes, "apply_entity_flags", lambda result, text: result)
    return create_app().test_client()


def test_api_check_includes_online_flags(monkeypatch, client):
    monkeypatch.setattr(routes, "online_flags", lambda text: [("new_domain", 20)])
    body = client.post("/api/check", json={"text": "Apply at https://jobs.example.com"}).get_json()
    assert "new_domain" in body["flags"]


def test_api_check_survives_online_failures(monkeypatch, client):
    def boom(text):
        raise RuntimeError("network down")
    monkeypatch.setattr(routes, "online_flags", boom)
    resp = client.post("/api/check", json={"text": "Pay the processing fee at irembo-gov.com"})
    assert resp.status_code == 200
    assert "impersonates_official_site" in resp.get_json()["flags"]
