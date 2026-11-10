# OWNER: Abay
import pytest

from app import auth, create_app, lookup, routes

HIGH_RISK_TEXT = "Guaranteed visa, pay the processing fee"  # upfront_fee + guaranteed_outcome = 60


@pytest.fixture
def saved():
    """Every check the route tries to save ends up in this list."""
    return []


@pytest.fixture
def client(monkeypatch, saved):
    def fake_save_check(masked_text, context, risk_score, verdict, flags,
                        channel="web", language="en"):
        saved.append({
            "masked_text": masked_text,
            "context": context,
            "risk_score": risk_score,
            "verdict": verdict,
            "flags": flags,
            "channel": channel,
            "language": language,
        })
        return len(saved)


    monkeypatch.setattr(routes.db, "save_check", fake_save_check)
    monkeypatch.setattr(routes.db, "find_risky_entities", lambda text: [])
    monkeypatch.setattr(lookup, "fetch_entities", lambda pairs: [])
    monkeypatch.setattr(lookup, "record_report", lambda pairs: None)
    monkeypatch.setenv("ENTITY_HASH_KEY", "test-entity-key")
    monkeypatch.setenv("COOKIE_SECURE", "false")  # the test client talks plain http

    monkeypatch.setattr(routes, "save_check", fake_save_check)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()



@pytest.fixture
def admin_session(client, monkeypatch):
    """Signs the test client in as an admin; the session lives in its cookie jar."""
    admin = {
        "id": 1,
        "email": "admin@genzura.test",
        "password_hash": generate_password_hash("secret123"),
        "role": "admin",
    }
    monkeypatch.setattr(auth, "_store_get_admin", lambda email: admin)
    res = client.post("/api/admin/login",
                      json={"email": "admin@genzura.test", "password": "secret123"})
    assert res.status_code == 200


# ---------- health ----------

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "Genzura API is running"}


def test_check_returns_expected_shape(client):
    res = client.post("/api/check", json={"text": "hello", "context": "job"})
    body = res.get_json()
    assert res.status_code == 200
    assert {"risk_score", "verdict", "flags", "check_id"} <= set(body.keys())


def test_check_flags_high_risk_message(client):
    body = client.post("/api/check", json={"text": HIGH_RISK_TEXT, "context": "visa"}).get_json()
    assert body["verdict"] == "high_risk"
    assert set(body["flags"]) == {"upfront_fee", "guaranteed_outcome"}


def test_check_defaults_to_job_context_and_english(client, saved):
    res = client.post("/api/check", json={"text": "hello"})
    assert res.status_code == 200
    assert saved[0]["context"] == "job"
    assert saved[0]["language"] == "en"
    assert saved[0]["channel"] == "web"


@pytest.mark.parametrize("payload,error", [
    ({}, "text is required"),
    ({"text": "   "}, "text is required"),
    ({"text": "hi", "context": "loan"}, "context must be job, scholarship, or visa"),
    ({"text": "hi", "language": "fr"}, "language must be en or rw"),
])
def test_check_validation_errors(client, payload, error):
    res = client.post("/api/check", json=payload)
    assert res.status_code == 400
    assert res.get_json() == {"error": error}


def test_check_without_json_body_is_400(client):
    assert client.post("/api/check").status_code == 400


def test_check_scores_raw_text_but_stores_masked_text(client, saved):
    text = "Contact hr@gmail.com or +250788123456 to pay the registration fee"
    body = client.post("/api/check", json={"text": text}).get_json()

    assert "free_email_contact" in body["flags"]  # scored on the raw text
    stored = saved[0]["masked_text"]
    assert "hr@gmail.com" not in stored
    assert "+250788123456" not in stored
    assert "[EMAIL]" in stored and "[PHONE]" in stored


def test_check_still_responds_when_database_save_fails(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(routes, "save_check", boom)
    res = client.post("/api/check", json={"text": "hello"})
    assert res.status_code == 200
    assert res.get_json()["check_id"] is None


def test_check_adds_blacklisted_entity_flag(client, monkeypatch):
    monkeypatch.setattr(routes.db, "find_risky_entities",
                        lambda text: [{"name": "ScamCo", "status": "blacklisted"}])
    body = client.post("/api/check", json={"text": "hello from ScamCo"}).get_json()
    assert body["flags"] == ["blacklisted_entity"]
    assert body["risk_score"] == 50
    assert body["verdict"] == "suspicious"


def test_check_adds_flagged_entity_flag(client, monkeypatch):
    monkeypatch.setattr(routes.db, "find_risky_entities",
                        lambda text: [{"name": "ShadyLtd", "status": "flagged"}])
    body = client.post("/api/check", json={"text": "hello from ShadyLtd"}).get_json()
    assert body["flags"] == ["flagged_entity"]
    assert body["risk_score"] == 25
    assert body["verdict"] == "low_risk"


def test_check_falls_back_to_rules_when_entity_lookup_fails(client, monkeypatch):
    def boom(text):
        raise RuntimeError("db down")

    monkeypatch.setattr(routes.db, "find_risky_entities", boom)
    res = client.post("/api/check", json={"text": HIGH_RISK_TEXT})
    assert res.status_code == 200
    assert res.get_json()["verdict"] == "high_risk"


@pytest.mark.parametrize("body", [
    {"text": 123}, {"text": 0}, {"text": True}, {"text": ["hello"]}, {"text": {"a": 1}},
])
def test_check_rejects_non_string_text_with_400(client, body):
    res = client.post("/api/check", json=body)
    assert res.status_code == 400
    assert res.get_json() == {"error": "text must be a string"}


@pytest.mark.parametrize("body,error", [
    ({"text": "hi", "context": 5}, "context must be a string"),
    ({"text": "hi", "context": ["job"]}, "context must be a string"),
    ({"text": "hi", "language": 1}, "language must be a string"),
    ({"text": "hi", "language": None}, "language must be a string"),
])
def test_check_rejects_non_string_context_or_language_with_400(client, body, error):
    res = client.post("/api/check", json=body)
    assert res.status_code == 400
    assert res.get_json() == {"error": error}


def test_check_rejects_text_over_2000_characters(client):
    assert client.post("/api/check", json={"text": "x" * 2000}).status_code == 200
    res = client.post("/api/check", json={"text": "x" * 2001})
    assert res.status_code == 400
    assert res.get_json() == {"error": "text must be at most 2000 characters"}


# ---------- /api/verify ----------

def test_verify_requires_a_real_name(client):
    assert client.get("/api/verify?name=a").status_code == 400
    assert client.get("/api/verify").status_code == 400


def test_verify_returns_matches(client, monkeypatch):
    rows = [{"id": 1, "name": "Acme Ltd", "type": "employer",
             "website": None, "status": "verified", "notes": None}]
    monkeypatch.setattr(routes.db, "find_entities", lambda q: rows)
    body = client.get("/api/verify?name=acme").get_json()
    assert body == {"query": "acme", "matches": rows}


def test_verify_returns_503_when_database_fails(client, monkeypatch):
    def boom(q):
        raise RuntimeError("db down")

    monkeypatch.setattr(routes.db, "find_entities", boom)
    assert client.get("/api/verify?name=acme").status_code == 503


# ---------- /api/report ----------

def test_report_validation(client):
    assert client.post("/api/report", json={"description": "short"}).status_code == 400
    res = client.post("/api/report",
                      json={"description": "A long enough description", "check_id": "7"})
    assert res.status_code == 400


def test_report_is_created_with_masked_description(client, monkeypatch):
    calls = []

    def fake_create_report(description, check_id=None):
        calls.append((description, check_id))
        return {"id": 1, "status": "new"}

    monkeypatch.setattr(routes.db, "create_report", fake_create_report)
    res = client.post("/api/report", json={
        "description": "Someone at hr@gmail.com asked me to pay a fee",
        "check_id": 3,
    })
    assert res.status_code == 201
    assert res.get_json() == {"id": 1, "status": "new"}
    description, check_id = calls[0]
    assert "hr@gmail.com" not in description and "[EMAIL]" in description
    assert check_id == 3


def test_report_returns_500_when_database_fails(client, monkeypatch):
    def boom(description, check_id=None):
        raise RuntimeError("db down")

    monkeypatch.setattr(routes.db, "create_report", boom)
    res = client.post("/api/report", json={"description": "A long enough description"})
    assert res.status_code == 500


# ---------- /api/ussd ----------

def ussd(client, text):
    return client.post("/api/ussd", data={"text": text})


def test_ussd_first_screen_is_menu(client):
    res = ussd(client, "")
    body = res.get_data(as_text=True)
    assert res.status_code == 200
    assert res.mimetype == "text/plain"
    assert body.startswith("CON ")
    assert "1. Job offer" in body


def test_ussd_invalid_choice_ends_session(client):
    assert ussd(client, "9").get_data(as_text=True).startswith("END ")


def test_ussd_asks_for_message_after_choice(client):
    body = ussd(client, "1").get_data(as_text=True)
    assert body.startswith("CON ") and "message" in body


def test_ussd_returns_verdict_and_saves_check(client, saved):
    body = ussd(client, "1*Guaranteed job, pay registration fee").get_data(as_text=True)
    assert body.startswith("END ")
    assert "HIGH RISK" in body
    assert saved[0]["channel"] == "ussd"
    assert saved[0]["context"] == "job"


def test_ussd_keeps_asterisks_typed_in_the_message(client, saved):
    ussd(client, "2*a*b")
    assert saved[0]["context"] == "scholarship"
    assert saved[0]["masked_text"] == "a*b"


# ---------- /api/sms ----------

@pytest.fixture
def sent(monkeypatch):
    messages = []
    monkeypatch.setattr(routes, "send_sms", lambda to, msg: messages.append((to, msg)) or True)
    return messages


def test_sms_uses_context_prefix_and_replies(client, saved, sent):
    res = client.post("/api/sms", data={"from": "+250788000000", "text": f"VISA {HIGH_RISK_TEXT}"})
    assert res.status_code == 200
    assert saved[0]["channel"] == "sms"
    assert saved[0]["context"] == "visa"
    to, message = sent[0]
    assert to == "+250788000000"
    assert "HIGH RISK" in message


def test_sms_defaults_to_job_without_prefix(client, saved, sent):
    client.post("/api/sms", data={"from": "+250788000000", "text": HIGH_RISK_TEXT})
    assert saved[0]["context"] == "job"
    assert saved[0]["masked_text"] == HIGH_RISK_TEXT


def test_sms_with_empty_text_does_nothing(client, saved, sent):
    res = client.post("/api/sms", data={"from": "+250788000000", "text": "  "})
    assert res.status_code == 200
    assert saved == [] and sent == []


# ---------- admin routes (login itself is tested in test_auth.py) ----------

def test_admin_routes_require_a_session(client):
    assert client.get("/api/admin/stats").status_code == 401
    bad = {"Cookie": "genzura_session=not-a-real-token"}
    assert client.get("/api/admin/stats", headers=bad).status_code == 401


def test_admin_session_opens_admin_routes(client, admin_session, monkeypatch):
    monkeypatch.setattr(routes.db, "get_stats", lambda: {"total_checks": 3})
    res = client.get("/api/admin/stats")
    assert res.status_code == 200
    assert res.get_json() == {"total_checks": 3}


def test_admin_reports_list_validates_status(client, admin_session, monkeypatch):
    seen = {}

    def fake_list_reports(status, limit, offset):
        seen.update(status=status, limit=limit, offset=offset)
        return []

    monkeypatch.setattr(routes.db, "list_reports", fake_list_reports)

    assert client.get("/api/admin/reports?status=bogus").status_code == 400

    res = client.get("/api/admin/reports?status=new&limit=999")
    assert res.status_code == 200
    assert seen == {"status": "new", "limit": 200, "offset": 0}  # limit is capped at 200


def test_admin_update_report_status(client, admin_session, monkeypatch):
    url = "/api/admin/reports/5"

    assert client.patch(url, json={"status": "bogus"}).status_code == 400
    assert client.patch(url, json={"status": ["closed"]}).status_code == 400

    monkeypatch.setattr(routes.db, "update_report_status", lambda rid, status: None)
    assert client.patch(url, json={"status": "closed"}).status_code == 404

    monkeypatch.setattr(routes.db, "update_report_status",
                        lambda rid, status: {"id": rid, "status": status})
    res = client.patch(url, json={"status": "closed"})
    assert res.status_code == 200
    assert res.get_json() == {"id": 5, "status": "closed"}


def test_admin_update_report_requires_a_session(client):
    assert client.patch("/api/admin/reports/5", json={"status": "closed"}).status_code == 401
