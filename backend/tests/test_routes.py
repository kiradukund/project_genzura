import pytest

from app import create_app, routes

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

    monkeypatch.setattr(routes, "save_check", fake_save_check)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


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
