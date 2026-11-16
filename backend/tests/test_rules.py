# OWNER: Abay
import pytest

from app.rules import add_flag, evaluate, verdict_for


def test_evaluate_returns_expected_keys():
    result = evaluate("any text", "job")
    assert {"risk_score", "verdict", "flags"} <= set(result.keys())


def test_benign_message_is_low_risk():
    result = evaluate("We are hiring a developer. Apply on our website.", "job")
    assert result == {"risk_score": 0, "verdict": "low_risk", "flags": []}


@pytest.mark.parametrize("text", ["", None])
def test_empty_or_none_text_is_low_risk(text):
    result = evaluate(text)
    assert result["risk_score"] == 0
    assert result["verdict"] == "low_risk"
    assert result["flags"] == []


def test_upfront_fee_is_flagged_and_suspicious():
    result = evaluate("Pay a registration fee via MoMo to secure your slot")
    assert result["flags"] == ["upfront_fee"]
    assert result["risk_score"] == 40
    assert result["verdict"] == "suspicious"


def test_matching_is_case_insensitive():
    assert "upfront_fee" in evaluate("WESTERN UNION only")["flags"]


def test_suspicious_verdict_from_combined_rules():
    # guaranteed_outcome (20) + urgency_pressure (15) = 35
    result = evaluate("Guaranteed job, apply urgently")
    assert set(result["flags"]) == {"guaranteed_outcome", "urgency_pressure"}
    assert result["risk_score"] == 35
    assert result["verdict"] == "suspicious"


def test_high_risk_verdict_at_threshold():
    # upfront_fee (40) + guaranteed_outcome (20) = 60
    result = evaluate("Guaranteed visa, pay the processing fee")
    assert result["risk_score"] == 60
    assert result["verdict"] == "high_risk"


def test_score_is_capped_at_100():
    text = ("URGENT: guaranteed job, pay registration fee via WhatsApp, "
            "send your passport to hr@gmail.com")
    result = evaluate(text)
    assert set(result["flags"]) == {
        "upfront_fee", "guaranteed_outcome", "urgency_pressure",
        "free_email_contact", "chat_app_only", "sensitive_info_request",
    }
    assert result["risk_score"] == 100
    assert result["verdict"] == "high_risk"


def test_sensitive_info_request_matches_across_lines():
    result = evaluate("Please send\nyour bank account details")
    assert "sensitive_info_request" in result["flags"]


def test_kinyarwanda_rules_match():
    # upfront_fee (40) + urgency_pressure (15) = 55
    result = evaluate("Ohereza amafaranga byihutirwa")
    assert set(result["flags"]) == {"upfront_fee", "urgency_pressure"}
    assert result["risk_score"] == 55
    assert result["verdict"] == "suspicious"


def test_same_flag_counts_once_across_languages():
    result = evaluate("Pay the registration fee, ohereza amafaranga")
    assert result["flags"].count("upfront_fee") == 1
    assert result["risk_score"] == 40


@pytest.mark.parametrize("score,verdict", [
    (0, "low_risk"),
    (29, "low_risk"),
    (30, "suspicious"),
    (59, "suspicious"),
    (60, "high_risk"),
    (100, "high_risk"),
])
def test_verdict_for_boundaries(score, verdict):
    assert verdict_for(score) == verdict


def test_add_flag_adds_weight_and_recomputes_verdict():
    base = {"risk_score": 20, "verdict": "low_risk", "flags": ["guaranteed_outcome"]}
    result = add_flag(base, "flagged_entity", 15)
    assert result == {
        "risk_score": 35,
        "verdict": "suspicious",
        "flags": ["guaranteed_outcome", "flagged_entity"],
    }
    # the input is not mutated
    assert base["risk_score"] == 20
    assert base["flags"] == ["guaranteed_outcome"]


def test_add_flag_is_idempotent():
    base = {"risk_score": 50, "verdict": "suspicious", "flags": ["blacklisted_entity"]}
    assert add_flag(base, "blacklisted_entity", 50) == base


def test_add_flag_caps_at_100():
    base = {"risk_score": 90, "verdict": "high_risk", "flags": ["upfront_fee"]}
    assert add_flag(base, "blacklisted_entity", 50)["risk_score"] == 100