# OWNER: Kevin
import pytest

from app import create_app, partner

GOOD_KEY = "gz_test_key"
HIGH_RISK_TEXT = "Guaranteed visa, pay the processing fee"


@pytest.fixture
def state():
    return {"saved": [], "requests_today": 0, "daily_limit": 3, "db_down": False}


@pytest.fixture
def client(monkeypatch, state):
    def fake_use_key(key):
        if state["db_down"]:
            raise RuntimeError("database down")
        if key != GOOD_KEY:
            return None
        state["requests_today"] += 1
        return {"id": 1, "partner_name": "Test partner",
                "requests_today": state["requests_today"], "daily_limit": state["daily_limit"]}

    def fake_save_check(masked_text, context, risk_score, verdict, flags,
                        channel="web", language="en"):
        state["saved"].append({"masked_text": masked_text, "channel": channel})
        return len(state["saved"])

    monkeypatch.setattr(partner, "use_key", fake_use_key)
    monkeypatch.setattr(partner, "save_check", fake_save_check)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def post(client, body, key=GOOD_KEY):
    headers = {"X-API-Key": key} if key else {}
    return client.post("/v1/check", json=body, headers=headers)


def test_missing_key_is_401(client):
    assert post(client, {"text": "hi"}, key=None).status_code == 401


def test_wrong_key_is_401(client):
    assert post(client, {"text": "hi"}, key="gz_wrong").status_code == 401


def test_valid_key_returns_result(client, state):
    res = post(client, {"text": HIGH_RISK_TEXT, "context": "visa"})
    body = res.get_json()
    assert res.status_code == 200
    assert body["verdict"] == "high_risk"
    assert body["check_id"] == 1
    assert body["requests_remaining_today"] == 2
    assert state["saved"][0]["channel"] == "api"


def test_text_is_masked_before_saving(client, state):
    post(client, {"text": "Pay the fee, email agent@gmail.com"})
    assert "agent@gmail.com" not in state["saved"][0]["masked_text"]


def test_daily_limit_is_429(client):
    for _ in range(3):
        assert post(client, {"text": "hello"}).status_code == 200
    assert post(client, {"text": "hello"}).status_code == 429


def test_database_down_is_503(client, state):
    state["db_down"] = True
    assert post(client, {"text": "hello"}).status_code == 503


@pytest.mark.parametrize("body", [
    {},
    {"text": ""},
    {"text": 123},
    {"text": "x" * 2001},
    {"text": "hi", "context": ["job"]},
    {"text": "hi", "context": "travel"},
    {"text": "hi", "language": "fr"},
])
def test_bad_input_is_400(client, body):
    assert post(client, body).status_code == 400


def test_non_object_body_is_400(client):
    assert post(client, ["text"]).status_code == 400


def test_key_is_hashed():
    assert partner.hash_key("abc") != "abc"
    assert len(partner.hash_key("abc")) == 64
