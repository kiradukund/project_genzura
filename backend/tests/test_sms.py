# OWNER: Kuol
import pytest
import requests

from app import alerts, create_app, messages, sms

CHECK = {"verdict": "high_risk", "flags": ["upfront_fee"], "risk_score": 60}


@pytest.fixture
def state():
    return {"sent": [], "saved": [], "checks": {7: CHECK}, "unsubscribed": []}


@pytest.fixture
def client(monkeypatch, state):
    monkeypatch.setenv("AT_USERNAME", "sandbox")
    monkeypatch.setenv("AT_API_KEY", "test-key")
    monkeypatch.setattr(sms, "send_sms", lambda phone, msg: state["sent"].append((phone, msg)))
    monkeypatch.setattr(sms, "get_check", lambda check_id: state["checks"].get(check_id))
    monkeypatch.setattr(sms, "limiter", sms.RateLimiter(3, 60))

    def fake_save_check(masked_text, context, risk_score, verdict, flags,
                        channel="web", language="en"):
        state["saved"].append({"masked_text": masked_text, "channel": channel, "language": language})
        return len(state["saved"])

    monkeypatch.setattr(sms, "save_check", fake_save_check)
    monkeypatch.setattr(alerts, "unsubscribe", lambda phone: state["unsubscribed"].append(phone))
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---- phone numbers ----------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("0788123456", "+250788123456"),
    ("0788 123 456", "+250788123456"),
    ("250788123456", "+250788123456"),
    ("+250 72-212-3456", "+250722123456"),
    ("0711123456", None),     # not a Rwandan mobile prefix
    ("078812345", None),      # too short
    ("+254712345678", None),  # Kenya
    ("", None),
    (None, None),
    (788123456, None),
])
def test_normalize_phone(raw, expected):
    assert sms.normalize_phone(raw) == expected


# ---- /api/send-result -------------------------------------------------------

def test_send_result_texts_the_check(client, state):
    res = client.post("/api/send-result", json={"phone": "0788123456", "check_id": 7, "language": "en"})
    assert res.status_code == 200
    assert res.get_json() == {"sent": True}
    assert state["sent"] == [("+250788123456", messages.sms_result("en", CHECK))]


def test_send_result_in_kinyarwanda(client, state):
    client.post("/api/send-result", json={"phone": "0788123456", "check_id": 7, "language": "rw"})
    assert state["sent"][0][1] == messages.sms_result("rw", CHECK)


@pytest.mark.parametrize("payload,status", [
    ({"phone": "123", "check_id": 7}, 400),
    ({"phone": "0788123456"}, 400),
    ({"phone": "0788123456", "check_id": None}, 400),
    ({"phone": "0788123456", "check_id": "7"}, 400),
    ({"phone": "0788123456", "check_id": True}, 400),
    ({"phone": "0788123456", "check_id": 7, "language": "fr"}, 400),
    ({"phone": "0788123456", "check_id": 99}, 404),
])
def test_send_result_rejects_bad_input(client, state, payload, status):
    assert client.post("/api/send-result", json=payload).status_code == status
    assert state["sent"] == []


def test_send_result_without_json_is_400(client):
    assert client.post("/api/send-result", data="x").status_code == 400


def test_send_result_is_off_without_settings(client, monkeypatch, state):
    monkeypatch.delenv("AT_API_KEY")
    res = client.post("/api/send-result", json={"phone": "0788123456", "check_id": 7})
    assert res.status_code == 503
    assert state["sent"] == []


def test_send_result_limits_messages_per_phone(client, state):
    body = {"phone": "0788123456", "check_id": 7}
    codes = [client.post("/api/send-result", json=body).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    assert len(state["sent"]) == 3


def test_send_result_reports_provider_failure(client, monkeypatch):
    def fail(phone, msg):
        raise sms.SmsError("down")

    monkeypatch.setattr(sms, "send_sms", fail)
    res = client.post("/api/send-result", json={"phone": "0788123456", "check_id": 7})
    assert res.status_code == 502


def test_send_result_database_down(client, monkeypatch):
    def boom(check_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(sms, "get_check", boom)
    res = client.post("/api/send-result", json={"phone": "0788123456", "check_id": 7})
    assert res.status_code == 503


# ---- inbound SMS ------------------------------------------------------------

def inbound(client, text, sender="+250788123456"):
    res = client.post("/api/sms/inbound", data={"from": sender, "to": "12345", "text": text, "id": "1"})
    assert res.status_code == 200
    return res


def test_inbound_checks_offer_and_replies(client, state):
    inbound(client, "Guaranteed visa, pay the processing fee")
    assert state["saved"][0]["channel"] == "sms"
    phone, msg = state["sent"][0]
    assert phone == "+250788123456"
    assert msg.startswith("Genzura: HIGH RISK")
    assert len(msg) <= 160


def test_inbound_rw_prefix_replies_in_kinyarwanda(client, state):
    inbound(client, "RW Ohereza amafaranga yo kwiyandikisha")
    assert state["saved"][0]["language"] == "rw"
    assert state["saved"][0]["masked_text"] == "Ohereza amafaranga yo kwiyandikisha"
    assert "IBYAGO" in state["sent"][0][1]


def test_inbound_does_not_store_phone_numbers(client, state):
    inbound(client, "Call 0788999999 to pay the registration fee")
    assert "0788999999" not in state["saved"][0]["masked_text"]


@pytest.mark.parametrize("word", ["STOP", "stop", " Stop ", "HAGARIKA"])
def test_inbound_stop_unsubscribes(client, state, word):
    inbound(client, word)
    assert state["unsubscribed"] == ["+250788123456"]
    assert state["sent"] == [] and state["saved"] == []


def test_inbound_empty_text_is_ignored(client, state):
    inbound(client, "   ")
    assert state["sent"] == [] and state["saved"] == []


# ---- Africa's Talking request -----------------------------------------------

class FakeResponse:
    def __init__(self, body, status=201):
        self.body = body
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self.body


def ok_body(status="Success"):
    return {"SMSMessageData": {"Recipients": [{"status": status, "statusCode": 101}]}}


def test_send_sms_uses_sandbox_and_api_key(monkeypatch):
    calls = []
    monkeypatch.setenv("AT_USERNAME", "sandbox")
    monkeypatch.setenv("AT_API_KEY", "k")
    monkeypatch.setenv("AT_SENDER_ID", "GENZURA")
    monkeypatch.setattr(sms.requests, "post",
                        lambda url, **kw: calls.append((url, kw)) or FakeResponse(ok_body()))
    sms.send_sms("+250788123456", "hello")
    url, kw = calls[0]
    assert url == sms.SANDBOX_URL
    assert kw["headers"]["apiKey"] == "k"
    assert kw["data"] == {"username": "sandbox", "to": "+250788123456", "message": "hello", "from": "GENZURA"}


def test_send_sms_uses_live_url_for_real_account(monkeypatch):
    calls = []
    monkeypatch.setenv("AT_USERNAME", "genzura")
    monkeypatch.setenv("AT_API_KEY", "k")
    monkeypatch.delenv("AT_SENDER_ID", raising=False)
    monkeypatch.setattr(sms.requests, "post",
                        lambda url, **kw: calls.append(url) or FakeResponse(ok_body()))
    sms.send_sms("+250788123456", "hello")
    assert calls == [sms.LIVE_URL]


@pytest.mark.parametrize("response", [
    FakeResponse(ok_body("InsufficientBalance")),
    FakeResponse({"SMSMessageData": {"Recipients": []}}),
    FakeResponse({"unexpected": True}),
    FakeResponse({}, status=401),
])
def test_send_sms_raises_when_not_accepted(monkeypatch, response):
    monkeypatch.setenv("AT_USERNAME", "sandbox")
    monkeypatch.setenv("AT_API_KEY", "k")
    monkeypatch.setattr(sms.requests, "post", lambda url, **kw: response)
    with pytest.raises(sms.SmsError):
        sms.send_sms("+250788123456", "hello")


def test_send_sms_raises_on_network_error(monkeypatch):
    monkeypatch.setenv("AT_USERNAME", "sandbox")
    monkeypatch.setenv("AT_API_KEY", "k")

    def down(url, **kw):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(sms.requests, "post", down)
    with pytest.raises(sms.SmsError):
        sms.send_sms("+250788123456", "hello")


def test_send_sms_needs_settings(monkeypatch):
    monkeypatch.delenv("AT_USERNAME", raising=False)
    monkeypatch.delenv("AT_API_KEY", raising=False)
    with pytest.raises(sms.SmsError):
        sms.send_sms("+250788123456", "hello")


def test_rate_limiter_forgets_old_sends(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(sms.time, "monotonic", lambda: clock[0])
    limiter = sms.RateLimiter(2, 60)
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")
    clock[0] += 61
    assert limiter.allow("a")
