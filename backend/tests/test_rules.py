
from app.rules import evaluate


def test_clean_message_is_low_risk():
    text = "We invite applications for the Software Engineer role at our Kigali office. Apply on our official website."
    result = evaluate(text)
    assert result["verdict"] == "low_risk"
    assert result["flags"] == []


def test_obvious_scam_is_high_risk():
    text = "URGENT! Guaranteed job in Dubai. Pay a registration fee via Western Union. Contact us on WhatsApp."
    result = evaluate(text)
    assert result["verdict"] == "high_risk"
    assert "upfront_fee" in result["flags"]


def test_free_email_alone_stays_low_risk():
    result = evaluate("Send your CV to hr.jobs@gmail.com")
    assert "free_email_contact" in result["flags"]
    assert result["verdict"] == "low_risk"


def test_score_is_capped_at_100():
    text = "URGENT guaranteed job. Pay registration fee. Email jobs@gmail.com or WhatsApp. Send your passport."
    assert evaluate(text)["risk_score"] == 100