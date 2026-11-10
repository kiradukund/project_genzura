# OWNER: Alier
import pytest
from flask import Flask

from app import assess
from app.assess import QUESTIONS, assess_bp, score_answers, verdict_for

SAFE = {
    "contact": "company",
    "pay_before": "no",
    "payment_method": "not_asked",
    "interview": "yes",
    "official_website": "yes",
    "documents": "no",
}
WORST = {
    "contact": "personal_email",
    "pay_before": "yes",
    "payment_method": "untraceable",
    "interview": "no",
    "official_website": "no",
    "documents": "yes",
}


@pytest.fixture
def saved():
    """Every assessment the route tries to save ends up in this list."""
    return []


@pytest.fixture
def client(monkeypatch, saved):
    # A fake save, so these tests never touch a real database.
    def fake_save(context, answers, risk_score, verdict):
        saved.append({"context": context, "answers": answers,
                      "risk_score": risk_score, "verdict": verdict})
        return len(saved)

    monkeypatch.setattr(assess, "save_assessment", fake_save)
    app = Flask(__name__)
    app.register_blueprint(assess_bp)
    app.config["TESTING"] = True
    return app.test_client()


def test_safe_answers_are_low_risk():
    result, error = score_answers(SAFE)
    assert error is None
    assert result == {"risk_score": 0, "verdict": "low_risk", "flags": []}


def test_worst_answers_are_high_risk_and_capped_at_100():
    result, _ = score_answers(WORST)
    assert result["risk_score"] == 100
    assert result["verdict"] == "high_risk"
    assert result["flags"] == [q["id"] for q in QUESTIONS]


def test_paying_before_travel_alone_is_medium_risk():
    result, _ = score_answers(dict(SAFE, pay_before="yes"))
    assert result["risk_score"] == 30
    assert result["verdict"] == "suspicious"
    assert result["flags"] == ["pay_before"]


@pytest.mark.parametrize(
    "score,verdict",
    [(0, "low_risk"), (24, "low_risk"), (25, "suspicious"), (49, "suspicious"),
     (50, "high_risk"), (100, "high_risk")],
)
def test_thresholds(score, verdict):
    assert verdict_for(score) == verdict


def test_every_question_has_a_risky_and_a_safe_answer():
    for q in QUESTIONS:
        points = q["answers"].values()
        assert min(points) == 0, q["id"]
        assert max(points) > 0, q["id"]


def test_endpoint_returns_the_result(client):
    res = client.post("/api/assess", json={"answers": WORST, "context": "visa"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["verdict"] == "high_risk"
    assert body["context"] == "visa"


def test_context_defaults_to_job(client):
    res = client.post("/api/assess", json={"answers": SAFE})
    assert res.get_json()["context"] == "job"


@pytest.mark.parametrize(
    "payload",
    [
        None,                                          # no body
        {"answers": "yes"},                            # answers is not an object
        {"answers": {"contact": "company"}},           # questions missing
        {"answers": dict(SAFE, contact="carrier pigeon")},  # unknown answer
        {"answers": dict(SAFE, contact=["company"])},  # wrong type
        {"answers": SAFE, "context": "holiday"},       # unknown offer type
    ],
)
def test_bad_requests_are_rejected(client, payload):
    res = client.post("/api/assess", json=payload) if payload else client.post("/api/assess")
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_assessment_is_saved_without_extra_fields(client, saved):
    answers = dict(WORST, name="Jane", phone="0788000000")  # extra fields must not be saved
    res = client.post("/api/assess", json={"answers": answers, "context": "scholarship"})
    assert res.get_json()["assessment_id"] == 1
    assert saved == [{"context": "scholarship", "answers": WORST,
                      "risk_score": 100, "verdict": "high_risk"}]


def test_bad_request_is_not_saved(client, saved):
    client.post("/api/assess", json={"answers": {"contact": "company"}})
    assert saved == []


def test_result_still_returned_if_database_is_down(client, monkeypatch):
    def broken_save(*args):
        raise RuntimeError("database is down")

    monkeypatch.setattr(assess, "save_assessment", broken_save)
    res = client.post("/api/assess", json={"answers": SAFE})
    assert res.status_code == 200
    assert res.get_json()["verdict"] == "low_risk"
    assert res.get_json()["assessment_id"] is None


def test_questions_endpoint_lists_questions_in_order(client):
    body = client.get("/api/assess/questions").get_json()
    assert [q["id"] for q in body] == [q["id"] for q in QUESTIONS]
    assert body[0]["answers"] == ["chat_app", "personal_email", "company", "in_person"]
