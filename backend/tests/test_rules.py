from app.rules import evaluate


def test_evaluate_returns_expected_keys():
    result = evaluate("any text", "job")
    assert {"risk_score", "verdict", "flags"} <= set(result.keys())
