# OWNER: Chol
from app.privacy import redact, strip_query_strings


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


def test_unspaced_rw_phone_redacted():
    assert redact("call 0788123456") == "call [PHONE]"
    assert redact("call 250788123456") == "call [PHONE]"


def test_normal_sentence_unchanged():
    text = "this offer looks suspicious"
    assert redact(text) == text


def test_query_string_stripped():
    assert strip_query_strings("https://example.com/apply?id=123&phone=0788") == "https://example.com/apply"


def test_query_string_stripped_before_storage():
    result = redact("apply at https://example.com/job?ref=abc&email=x@y.com")
    assert "ref=abc" not in result
