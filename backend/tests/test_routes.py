# OWNER: Abay
import pytest

from app import create_app, lookup, routes

HIGH_RISK_TEXT = "Guaranteed visa, pay the processing fee"  # upfront_fee + guaranteed_outcome = 60


@pytest.fixture
def saved():
    """The keyword arguments of every db.save_check call."""
    return []


@pytest.fixture
def client(monkeypatch, saved):
    def fake_save_check(**kwargs):
        saved.append(kwargs)
        return len(saved)

    # raising=False: the real save_check lives in Chol's db.py on dev
    monkeypatch.setattr(routes.db, "save_check", fake_save_check, raising=False)
    monkeypatch.setattr(lookup, "fetch_entities", lambda pairs: [])
    monkeypatch.setenv("ENTITY_HASH_KEY", "test-entity-key")
    monkeypatch.setenv("COOKIE_SECURE", "false")  # the test client talks plain http

    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------- health ----------

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "Genzura API is running"}


# ---------- /api/check ----------

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


def test_check_rejects_a_json_body_that_is_not_an_object(client):
    assert client.post("/api/check", json=["hello"]).status_code == 400


# ---------- /api/check: saving through db.save_check ----------

def test_check_saves_redacted_text_and_the_result(client, saved, monkeypatch):
    monkeypatch.setattr(routes, "redact", lambda t: t.replace("hr@gmail.com", "<email>"))
    body = client.post("/api/check", json={"text": "Mail hr@gmail.com to pay the registration fee"}).get_json()

    assert "free_email_contact" in body["flags"]            # scored on the original text
    assert saved[0]["masked_text"] == "Mail <email> to pay the registration fee"
    assert "hr@gmail.com" not in repr(saved)                # the original never reaches save_check
    assert saved[0]["risk_score"] == body["risk_score"]
    assert saved[0]["verdict"] == body["verdict"]
    assert saved[0]["flags"] == body["flags"]


@pytest.mark.parametrize("returned,expected", [
    (5, 5), ({"id": 9, "verdict": "low_risk"}, 9), (None, None), (True, None), ("x", None),
])
def test_check_id_accepts_whatever_save_check_returns(client, monkeypatch, returned, expected):
    monkeypatch.setattr(routes.db, "save_check", lambda **kwargs: returned, raising=False)
    assert client.post("/api/check", json={"text": "hello"}).get_json()["check_id"] == expected


def test_check_still_responds_when_save_check_fails(client, monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(routes.db, "save_check", boom, raising=False)
    res = client.post("/api/check", json={"text": "hello"})
    assert res.status_code == 200
    assert res.get_json()["check_id"] is None


def test_check_still_responds_when_save_check_has_a_different_signature(client, monkeypatch):
    def old_style(channel, context, language, masked_text, result):
        return 1

    monkeypatch.setattr(routes.db, "save_check", old_style, raising=False)
    res = client.post("/api/check", json={"text": HIGH_RISK_TEXT})
    assert res.status_code == 200
    assert res.get_json()["verdict"] == "high_risk"


def test_check_still_responds_when_redact_fails(client, monkeypatch):
    def boom(text):
        raise RuntimeError("redact failed")

    monkeypatch.setattr(routes, "redact", boom)
    res = client.post("/api/check", json={"text": "hello"})
    assert res.status_code == 200
    assert res.get_json()["check_id"] is None