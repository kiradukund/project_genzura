# OWNER: Kuol
import pytest

from app import create_app, messages, ussd

HIGH_RISK_TEXT = "Guaranteed visa, pay the processing fee"
USSD_MAX = 182


@pytest.fixture
def saved():
    return []


@pytest.fixture
def client(monkeypatch, saved):
    def fake_save_check(masked_text, context, risk_score, verdict, flags,
                        channel="web", language="en"):
        saved.append({"masked_text": masked_text, "context": context, "verdict": verdict,
                      "channel": channel, "language": language})
        return len(saved)

    monkeypatch.setattr(ussd, "save_check", fake_save_check)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def dial(client, text, phone="+250788123456"):
    """Send what Africa's Talking sends: form fields, everything typed joined by '*'."""
    res = client.post("/api/ussd", data={
        "sessionId": "ATUid_1", "serviceCode": "*384*123#", "phoneNumber": phone, "text": text,
    })
    assert res.status_code == 200
    assert res.mimetype == "text/plain"
    return res.get_data(as_text=True)


def test_first_screen_is_language_menu(client):
    assert dial(client, "") == "CON " + messages.LANGUAGE_MENU


@pytest.mark.parametrize("choice,lang", [("1", "en"), ("2", "rw")])
def test_language_choice_shows_main_menu(client, choice, lang):
    assert dial(client, choice) == "CON " + messages.text(lang, "main_menu")


def test_offer_type_asks_for_message(client):
    assert dial(client, "1*3") == "CON " + messages.text("en", "ask_message")


def test_full_session_returns_result_and_ends(client, saved):
    reply = dial(client, f"1*3*{HIGH_RISK_TEXT}")
    assert reply.startswith("END ")
    assert reply == "END " + messages.ussd_result("en", {"verdict": "high_risk", "flags": ["upfront_fee"]})
    assert saved[0]["channel"] == "ussd"
    assert saved[0]["context"] == "visa"
    assert saved[0]["verdict"] == "high_risk"


def test_kinyarwanda_session(client, saved):
    reply = dial(client, "2*1*Ohereza amafaranga yo kwiyandikisha byihutirwa")
    assert reply.startswith("END ")
    assert "166" in reply
    assert saved[0]["language"] == "rw"
    assert saved[0]["context"] == "job"


def test_message_containing_star_is_kept_whole(client, saved):
    dial(client, "1*1*Pay *registration fee* now")
    assert saved[0]["masked_text"] == "Pay *registration fee* now"


def test_phone_number_is_not_stored(client, saved):
    dial(client, "1*1*Call 0788123456 and pay the registration fee")
    assert "0788123456" not in saved[0]["masked_text"]


@pytest.mark.parametrize("text", ["9", "1*7", "1*", "1*2*   "])
def test_invalid_input_ends_session(client, text, saved):
    reply = dial(client, text)
    assert reply.startswith("END ")
    assert messages.text("en", "invalid") in reply
    assert saved == []


def test_invalid_choice_in_kinyarwanda(client):
    assert dial(client, "2*9") == "END " + messages.text("rw", "invalid")


def test_still_answers_when_database_is_down(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(ussd, "save_check", boom)
    assert dial(client, f"1*3*{HIGH_RISK_TEXT}").startswith("END ")


@pytest.mark.parametrize("text", ["", "1", "2", "1*1", "2*2", f"1*3*{HIGH_RISK_TEXT}", "2*3*hello"])
def test_every_screen_fits(client, text):
    assert len(dial(client, text)) - len("CON ") <= USSD_MAX
