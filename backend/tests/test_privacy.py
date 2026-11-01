from app.privacy import redact


def test_email_redacted():
    assert redact("contact me at john@example.com today") == "contact me at [EMAIL] today"


def test_rwandan_phone_redacted():
    assert "[PHONE]" in redact("call +250 788 123 456 now")


def test_name_redacted():
    assert redact("send money to John Doe please") == "send money to [NAME] please"


def test_date_not_redacted():
    result = redact("deadline is 2026-11-03")
    assert "[PHONE]" not in result
    assert result == "deadline is 2026-11-03"


def test_normal_sentence_unchanged():
    text = "this offer looks suspicious"
    assert redact(text) == text
