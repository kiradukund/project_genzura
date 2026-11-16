# OWNER: Alier - Guided assessment. Build: POST /api/assess
import logging

from flask import Blueprint, jsonify, request
from psycopg2.extras import Json

from .db import _get_conn

log = logging.getLogger(__name__)
assess_bp = Blueprint("assess", __name__)

# Each question has an id and the points for each answer.
# The words people read live in frontend/src/i18n/en.json and rw.json under "assess".
QUESTIONS = [
    {"id": "contact", "answers": {"chat_app": 10, "personal_email": 15, "company": 0, "in_person": 0}},
    {"id": "pay_before", "answers": {"yes": 30, "not_sure": 10, "no": 0}},
    {"id": "payment_method", "answers": {"untraceable": 25, "company_bank": 5, "not_asked": 0}},
    {"id": "interview", "answers": {"no": 15, "yes": 0}},
    {"id": "official_website", "answers": {"no": 15, "not_checked": 10, "yes": 0}},
    {"id": "documents", "answers": {"yes": 15, "no": 0}},
]

VALID_CONTEXTS = {"job", "scholarship", "visa"}
MAX_SCORE = 100


def verdict_for(score):
    """Approved thresholds: 50 or more is high, 25 to 49 is medium, under 25 is low."""
    if score >= 50:
        return "high_risk"
    if score >= 25:
        return "suspicious"
    return "low_risk"


def score_answers(answers):
    """Add up the points. Returns (result, error)."""
    if not isinstance(answers, dict):
        return None, "answers must be an object"

    score = 0
    flags = []
    for question in QUESTIONS:
        qid = question["id"]
        answer = answers.get(qid)
        if not isinstance(answer, str) or answer not in question["answers"]:
            return None, f"missing or unknown answer for '{qid}'"
        points = question["answers"][answer]
        if points:
            score += points
            flags.append(qid)

    score = min(score, MAX_SCORE)
    return {"risk_score": score, "verdict": verdict_for(score), "flags": flags}, None


def save_assessment(context, answers, risk_score, verdict):
    """Save one assessment (table from db/migrations/005_assess.sql). Returns its id."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO assessments (context, answers, risk_score, verdict)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (context, Json(answers), risk_score, verdict),
            )
            row_id = cur.fetchone()[0]
        conn.commit()
        return row_id
    finally:
        conn.close()


@assess_bp.route("/api/assess/questions", methods=["GET"])
def questions():
    """The question and answer ids, in order, so the page can show them."""
    return jsonify([{"id": q["id"], "answers": list(q["answers"])} for q in QUESTIONS])


@assess_bp.route("/api/assess", methods=["POST"])
def assess():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "body must be a JSON object"}), 400

    context = data.get("context", "job")
    if not isinstance(context, str) or context not in VALID_CONTEXTS:
        return jsonify({"error": "context must be job, scholarship, or visa"}), 400

    result, error = score_answers(data.get("answers"))
    if error:
        return jsonify({"error": error}), 400

    # Save only the known answer ids (never extra fields the client sent).
    answers = {q["id"]: data["answers"][q["id"]] for q in QUESTIONS}
    try:
        assessment_id = save_assessment(context, answers, result["risk_score"], result["verdict"])
    except Exception:
        # The user still gets their result if the database is down.
        log.exception("Could not save assessment")
        assessment_id = None

    return jsonify({**result, "context": context, "assessment_id": assessment_id})
