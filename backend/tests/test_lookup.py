# OWNER: Abay
import pytest

from app import create_app, lookup, routes

PHONE = "+250788123456"


@pytest.fixture(autouse=True)
def hash_key(monkeypatch):
    monkeypatch.setenv("ENTITY_HASH_KEY", "test-entity-key")


def row(kind, value, count=0, status="unknown"):
    return {"kind": kind, "value_hash": lookup.hash_value(kind, value),
            "report_count": count, "status": status}


# ---------- normalizing ----------

@pytest.mark.parametrize("raw,expected", [
    ("+250 788 123 456", PHONE),
    ("0788123456", PHONE),
    ("250788123456", PHONE),
    ("788123456", PHONE),
    ("00250788123456", PHONE),
    ("+1 (415) 555-2671", "+14155552671"),
    ("1199880012345678", None),   # 16-digit national ID
    ("12345678", None),           # too short
])
def test_normalize_phone(raw, expected):
    assert lookup.normalize_phone(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("https://www.Evil-Jobs.com/apply/?id=7#top", "evil-jobs.com/apply?id=7"),
    ("www.evil.com.", "evil.com"),
    ("bit.ly/3xYz", "bit.ly/3xYz"),   # the path stays case-sensitive
    ("http://localhost", None),
])
def test_normalize_link(raw, expected):
    assert lookup.normalize_link(raw) == expected


def test_normalize_email_lowercases():
    assert lookup.normalize_email(" HR@Gmail.COM ") == "hr@gmail.com"


# ---------- extracting ----------

def test_extract_finds_emails_links_and_phones():
    text = ("Contact HR@Gmail.com or call +250 788 123 456 (WhatsApp) "
            "and apply at https://visa-jobs.example/apply, ref 2026-11-10.")
    assert lookup.extract_entities(text) == [
        {"kind": "email", "value": "hr@gmail.com"},
        {"kind": "link", "value": "visa-jobs.example/apply"},
        {"kind": "phone", "value": PHONE},
    ]


def test_digits_inside_an_email_are_not_a_phone():
    assert lookup.extract_entities("write to john0788123456@gmail.com") == [
        {"kind": "email", "value": "john0788123456@gmail.com"}]


def test_national_id_is_not_extracted():
    assert lookup.extract_entities("My ID is 1199880012345678") == []


def test_same_contact_in_two_formats_is_one_entity():
    found = lookup.extract_entities("call 0788123456 or +250788123456")
    assert found == [{"kind": "phone", "value": PHONE}]


def test_extraction_is_capped():
    text = ", ".join(f"+25078{n:07d}" for n in range(30))
    assert len(lookup.extract_entities(text)) == lookup.MAX_ENTITIES


def test_extract_handles_empty_input():
    assert lookup.extract_entities("") == []
    assert lookup.extract_entities(None) == []


# ---------- hashing ----------

def test_hash_is_deterministic_and_hides_the_value():
    first = lookup.hash_value("phone", PHONE)
    assert first == lookup.hash_value("phone", PHONE)
    assert len(first) == 64
    assert "250788123456" not in first


def test_hash_depends_on_kind_and_key(monkeypatch):
    first = lookup.hash_value("phone", PHONE)
    assert lookup.hash_value("email", PHONE) != first
    monkeypatch.setenv("ENTITY_HASH_KEY", "another-key")
    assert lookup.hash_value("phone", PHONE) != first


def test_hashing_without_a_key_fails_loudly(monkeypatch):
    monkeypatch.delenv("ENTITY_HASH_KEY")
    with pytest.raises(RuntimeError):
        lookup.hash_value("phone", PHONE)


# ---------- assessing ----------

@pytest.mark.parametrize("status,count,expected", [
    ("blacklisted", 0, ("blacklisted_contact", 50)),
    ("blacklisted", 9, ("blacklisted_contact", 50)),
    ("flagged", 0, ("reported_contact", 25)),
    ("unknown", 2, ("reported_contact", 25)),
    ("unknown", 1, None),
    ("unknown", 0, None),
])
def test_assess(status, count, expected):
    assert lookup.assess({"status": status, "report_count": count}) == expected


def test_apply_entity_flags_without_contacts_skips_the_database(monkeypatch):
    def boom(pairs):
        raise AssertionError("should not query")

    monkeypatch.setattr(lookup, "fetch_entities", boom)
    base = {"risk_score": 0, "verdict": "low_risk", "flags": []}
    assert lookup.apply_entity_flags(base, "no contacts in here") == base


def test_apply_entity_flags_adds_flag_for_blacklisted_contact(monkeypatch):
    seen = []
    monkeypatch.setattr(lookup, "fetch_entities",
                        lambda pairs: seen.extend(pairs) or [row("phone", PHONE, status="blacklisted")])
    base = {"risk_score": 0, "verdict": "low_risk", "flags": []}
    result = lookup.apply_entity_flags(base, "call 0788123456 now")
    assert result == {"risk_score": 50, "verdict": "suspicious", "flags": ["blacklisted_contact"]}
    assert seen == [("phone", lookup.hash_value("phone", PHONE))]  # only hashes reach the database


def test_apply_entity_flags_ignores_a_single_report(monkeypatch):
    monkeypatch.setattr(lookup, "fetch_entities", lambda pairs: [row("phone", PHONE, count=1)])
    base = {"risk_score": 10, "verdict": "low_risk", "flags": ["chat_app_only"]}
    assert lookup.apply_entity_flags(base, "call 0788123456") == base


def test_reported_contact_flag_is_added_once(monkeypatch):
    monkeypatch.setattr(lookup, "fetch_entities", lambda pairs: [
        row("phone", PHONE, count=3), row("email", "hr@gmail.com", count=2)])
    base = {"risk_score": 0, "verdict": "low_risk", "flags": []}
    result = lookup.apply_entity_flags(base, "hr@gmail.com or 0788123456")
    assert result["flags"] == ["reported_contact"]
    assert result["risk_score"] == 25


# ---------- lookup() and report counting ----------

def test_lookup_describes_each_contact(monkeypatch):
    monkeypatch.setattr(lookup, "fetch_entities",
                        lambda pairs: [row("phone", PHONE, count=4, status="flagged")])
    out = lookup.lookup("call 0788123456 or mail new@scam.test")
    assert out == [
        {"kind": "email", "value": "new@scam.test", "known": False, "risky": False,
         "report_count": 0, "status": "unknown"},
        {"kind": "phone", "value": PHONE, "known": True, "risky": True,
         "report_count": 4, "status": "flagged"},
    ]


def test_record_report_entities_sends_only_hashes(monkeypatch):
    recorded = []
    monkeypatch.setattr(lookup, "record_report", lambda pairs: recorded.extend(pairs))
    count = lookup.record_report_entities("He called from 0788123456 and wrote to hr@gmail.com")
    assert count == 2
    assert ("phone", lookup.hash_value("phone", PHONE)) in recorded
    assert ("email", lookup.hash_value("email", "hr@gmail.com")) in recorded
    assert "250788123456" not in repr(recorded) and "hr@gmail.com" not in repr(recorded)


# ---------- routes ----------

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(routes.db, "save_check", lambda *a, **k: 1)
    monkeypatch.setattr(routes.db, "find_risky_entities", lambda text: [])
    monkeypatch.setattr(lookup, "fetch_entities", lambda pairs: [])
    monkeypatch.setattr(lookup, "record_report", lambda pairs: None)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_lookup_route_returns_entities(client, monkeypatch):
    monkeypatch.setattr(lookup, "fetch_entities",
                        lambda pairs: [row("phone", PHONE, status="blacklisted")])
    res = client.post("/api/lookup", json={"text": "call 0788123456"})
    assert res.status_code == 200
    assert res.get_json() == {"entities": [{
        "kind": "phone", "value": PHONE, "known": True, "risky": True,
        "report_count": 0, "status": "blacklisted"}]}


def test_lookup_route_with_no_contacts_returns_empty_list(client):
    res = client.post("/api/lookup", json={"text": "nothing to see"})
    assert res.get_json() == {"entities": []}


@pytest.mark.parametrize("payload", [
    {}, {"text": "  "}, {"text": 123}, {"text": ["a"]}, {"text": "x" * 2001},
])
def test_lookup_route_validation(client, payload):
    assert client.post("/api/lookup", json=payload).status_code == 400


def test_lookup_route_rejects_non_object_body(client):
    assert client.post("/api/lookup", json=["text"]).status_code == 400


def test_lookup_route_returns_503_when_database_fails(client, monkeypatch):
    def boom(pairs):
        raise RuntimeError("db down")

    monkeypatch.setattr(lookup, "fetch_entities", boom)
    res = client.post("/api/lookup", json={"text": "call 0788123456"})
    assert res.status_code == 503


def test_check_gets_a_flag_for_a_known_contact(client, monkeypatch):
    monkeypatch.setattr(lookup, "fetch_entities",
                        lambda pairs: [row("phone", PHONE, status="blacklisted")])
    body = client.post("/api/check", json={"text": "Call 0788123456 about the job"}).get_json()
    assert "blacklisted_contact" in body["flags"]
    assert body["verdict"] == "suspicious"


def test_check_still_works_when_contact_lookup_fails(client, monkeypatch):
    def boom(pairs):
        raise RuntimeError("db down")

    monkeypatch.setattr(lookup, "fetch_entities", boom)
    res = client.post("/api/check", json={"text": "Call 0788123456, guaranteed job"})
    assert res.status_code == 200
    assert "guaranteed_outcome" in res.get_json()["flags"]


def test_report_counts_the_contacts_it_mentions(client, monkeypatch):
    recorded = []
    monkeypatch.setattr(routes.db, "create_report", lambda description, check_id=None: {"id": 1})
    monkeypatch.setattr(lookup, "record_report", lambda pairs: recorded.extend(pairs))
    res = client.post("/api/report", json={"description": "Scammer called from 0788123456 asking for fees"})
    assert res.status_code == 201
    assert recorded == [("phone", lookup.hash_value("phone", PHONE))]


def test_report_is_saved_even_if_counting_fails(client, monkeypatch):
    def boom(pairs):
        raise RuntimeError("db down")

    monkeypatch.setattr(routes.db, "create_report", lambda description, check_id=None: {"id": 1})
    monkeypatch.setattr(lookup, "record_report", boom)
    res = client.post("/api/report", json={"description": "Scammer called from 0788123456 asking for fees"})
    assert res.status_code == 201