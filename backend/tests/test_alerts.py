# OWNER: Kuol
import pytest

from app import alerts, create_app, sms
from app.messages import MESSAGES, is_gsm7

TOKEN = "cron-secret"


@pytest.fixture
def state():
    return {
        "subscribers": {},  # phone -> {"language", "active"}
        "sent": [],
        "marked": [],
        "summary": {"count": 12, "top_flag": "upfront_fee"},
    }


@pytest.fixture
def client(monkeypatch, state):
    monkeypatch.setenv("AT_USERNAME", "sandbox")
    monkeypatch.setenv("AT_API_KEY", "test-key")
    monkeypatch.setenv("ALERTS_CRON_TOKEN", TOKEN)

    def save_subscriber(phone, language):
        state["subscribers"][phone] = {"language": language, "active": True}

    def unsubscribe(phone):
        phone = sms.normalize_phone(phone)
        sub = state["subscribers"].get(phone)
        if sub and sub["active"]:
            sub["active"] = False
            return True
        return False

    def active_subscribers():
        return [{"id": i, "phone": p, "language": s["language"]}
                for i, (p, s) in enumerate(state["subscribers"].items(), 1) if s["active"]]

    monkeypatch.setattr(alerts, "save_subscriber", save_subscriber)
    monkeypatch.setattr(alerts, "unsubscribe", unsubscribe)
    monkeypatch.setattr(alerts, "active_subscribers", active_subscribers)
    monkeypatch.setattr(alerts, "weekly_summary", lambda: state["summary"])
    monkeypatch.setattr(alerts, "mark_sent", lambda ids: state["marked"].extend(ids))
    monkeypatch.setattr(alerts, "send_sms", lambda phone, msg: state["sent"].append((phone, msg)))
    monkeypatch.setattr(alerts, "subscribe_limiter", sms.RateLimiter(3, 60))
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---- subscribe / unsubscribe ------------------------------------------------

def test_subscribe_saves_number_and_sends_welcome(client, state):
    res = client.post("/api/alerts/subscribe", json={"phone": "0788 123 456", "language": "rw"})
    assert res.status_code == 200
    assert res.get_json() == {"subscribed": True}
    assert state["subscribers"] == {"+250788123456": {"language": "rw", "active": True}}
    assert state["sent"] == [("+250788123456", alerts.ALERT_TEXT["rw"]["welcome"])]


def test_subscribe_works_without_sms_settings(client, monkeypatch, state):
    monkeypatch.delenv("AT_API_KEY")
    res = client.post("/api/alerts/subscribe", json={"phone": "0788123456"})
    assert res.status_code == 200
    assert "+250788123456" in state["subscribers"]
    assert state["sent"] == []


@pytest.mark.parametrize("payload", [
    {"phone": "12345"},
    {},
    {"phone": "0788123456", "language": "fr"},
])
def test_subscribe_rejects_bad_input(client, state, payload):
    assert client.post("/api/alerts/subscribe", json=payload).status_code == 400
    assert state["subscribers"] == {}


def test_subscribe_without_json_is_400(client):
    assert client.post("/api/alerts/subscribe", data="x").status_code == 400


def test_subscribe_is_rate_limited(client):
    body = {"phone": "0788123456"}
    codes = [client.post("/api/alerts/subscribe", json=body).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]


def test_subscribe_database_down(client, monkeypatch):
    def boom(phone, language):
        raise RuntimeError("db down")

    monkeypatch.setattr(alerts, "save_subscriber", boom)
    assert client.post("/api/alerts/subscribe", json={"phone": "0788123456"}).status_code == 503


def test_unsubscribe_gives_same_answer_for_unknown_number(client, state):
    client.post("/api/alerts/subscribe", json={"phone": "0788123456"})
    for phone in ("0788123456", "0722000000"):
        res = client.post("/api/alerts/unsubscribe", json={"phone": phone})
        assert res.status_code == 200
        assert res.get_json() == {"unsubscribed": True}
    assert state["subscribers"]["+250788123456"]["active"] is False


def test_unsubscribe_rejects_bad_number(client):
    assert client.post("/api/alerts/unsubscribe", json={"phone": "abc"}).status_code == 400


# ---- weekly send ------------------------------------------------------------

def test_weekly_send_needs_the_cron_token(client, state):
    client.post("/api/alerts/subscribe", json={"phone": "0788123456"})
    state["sent"].clear()
    assert client.post("/api/alerts/send-weekly").status_code == 403
    assert client.post("/api/alerts/send-weekly", headers={"X-Cron-Token": "wrong"}).status_code == 403
    assert state["sent"] == []


def test_weekly_send_is_off_without_token_setting(client, monkeypatch):
    monkeypatch.delenv("ALERTS_CRON_TOKEN")
    res = client.post("/api/alerts/send-weekly", headers={"X-Cron-Token": ""})
    assert res.status_code == 403


def test_weekly_send_texts_every_active_subscriber(client, state):
    client.post("/api/alerts/subscribe", json={"phone": "0788123456", "language": "en"})
    client.post("/api/alerts/subscribe", json={"phone": "0722123456", "language": "rw"})
    client.post("/api/alerts/subscribe", json={"phone": "0733123456"})
    client.post("/api/alerts/unsubscribe", json={"phone": "0733123456"})
    state["sent"].clear()

    res = client.post("/api/alerts/send-weekly", headers={"X-Cron-Token": TOKEN})
    assert res.status_code == 200
    assert res.get_json() == {"sent": 2, "failed": 0}
    sent = dict(state["sent"])
    assert "12 risky offers" in sent["+250788123456"]
    assert "Upfront payment requested" in sent["+250788123456"]
    assert "Basaba kwishyura mbere" in sent["+250722123456"]
    assert "+250733123456" not in sent
    assert state["marked"] == [1, 2]


def test_weekly_send_counts_failures(client, monkeypatch, state):
    client.post("/api/alerts/subscribe", json={"phone": "0788123456"})

    def fail(phone, msg):
        raise sms.SmsError("down")

    monkeypatch.setattr(alerts, "send_sms", fail)
    res = client.post("/api/alerts/send-weekly", headers={"X-Cron-Token": TOKEN})
    assert res.get_json() == {"sent": 0, "failed": 1}
    assert state["marked"] == []


def test_quiet_week_message(client, state):
    state["summary"] = {"count": 0, "top_flag": None}
    client.post("/api/alerts/subscribe", json={"phone": "0788123456"})
    state["sent"].clear()
    client.post("/api/alerts/send-weekly", headers={"X-Cron-Token": TOKEN})
    assert state["sent"][0][1] == alerts.ALERT_TEXT["en"]["quiet"]


# ---- text limits (feature phones) -------------------------------------------

@pytest.mark.parametrize("lang", ["en", "rw"])
@pytest.mark.parametrize("flag", list(MESSAGES["en"]["flags"]))
def test_alert_texts_fit_in_one_sms(lang, flag):
    texts = [alerts.alert_text(lang, "welcome"), alerts.alert_text(lang, "quiet"),
             alerts.weekly_message(lang, {"count": 9999, "top_flag": flag})]
    for text in texts:
        assert len(text) <= 160, text
        assert is_gsm7(text), text
