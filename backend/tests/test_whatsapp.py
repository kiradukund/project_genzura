# OWNER: Didier
import hashlib
import hmac
import json

import pytest

from app import create_app

SECRET = "test-app-secret"
SCAM = "Guaranteed visa, pay the processing fee"


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SECRET)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "my-verify-token")
    sent, saved = [], []
    monkeypatch.setattr("app.whatsapp.send_text", lambda to, body: sent.append((to, body)) or True)
    monkeypatch.setattr("app.whatsapp._save_check", lambda *a: saved.append(a) or 1)
    return sent, saved


def _client():
    return create_app().test_client()


def _payload(text, sender="250788000000"):
    return {"entry": [{"changes": [{"value": {"messages": [
        {"from": sender, "type": "text", "text": {"body": text}}
    ]}}]}]}


def _post(client, payload, secret=SECRET):
    raw = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return client.post("/api/whatsapp", data=raw,
                       headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})


# ---- Meta's one-time webhook check ----

def test_verify_ok(env):
    r = _client().get("/api/whatsapp?hub.mode=subscribe&hub.verify_token=my-verify-token&hub.challenge=12345")
    assert r.status_code == 200
    assert r.get_data(as_text=True) == "12345"


def test_verify_wrong_token(env):
    r = _client().get("/api/whatsapp?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=12345")
    assert r.status_code == 403


# ---- Signature ----

def test_bad_signature_rejected(env):
    sent, saved = env
    r = _post(_client(), _payload(SCAM), secret="not-the-secret")
    assert r.status_code == 403
    assert sent == [] and saved == []


def test_missing_signature_rejected(env):
    r = _client().post("/api/whatsapp", json=_payload(SCAM))
    assert r.status_code == 403


# ---- Messages ----

def test_scam_message_gets_reply_and_is_saved(env):
    sent, saved = env
    r = _post(_client(), _payload(SCAM))
    assert r.status_code == 200
    assert len(sent) == 1
    to, body = sent[0]
    assert to == "250788000000"
    assert "166" in body
    assert saved[0][0] == "whatsapp"


def test_status_update_is_ignored(env):
    sent, saved = env
    payload = {"entry": [{"changes": [{"value": {"statuses": [{"status": "read"}]}}]}]}
    r = _post(_client(), payload)
    assert r.status_code == 200
    assert sent == [] and saved == []


def test_long_text_is_cut(env):
    sent, saved = env
    _post(_client(), _payload("a" * 5000))
    assert len(saved[0][3]) == 2000
