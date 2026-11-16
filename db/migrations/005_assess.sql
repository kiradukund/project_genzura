-- OWNER: Alier - assessment questions
-- One row per guided assessment (POST /api/assess).
-- Privacy: no names, phone numbers, emails or message text. Only the offer
-- type, the chosen answer ids, the score and the risk level.

CREATE TABLE IF NOT EXISTS assessments (
    id          SERIAL PRIMARY KEY,
    context     VARCHAR(12) NOT NULL CHECK (context IN ('job', 'scholarship', 'visa')),
    answers     JSONB       NOT NULL,
    risk_score  INTEGER     NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    verdict     VARCHAR(12) NOT NULL CHECK (verdict IN ('low_risk', 'suspicious', 'high_risk')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- For counting recent assessments (e.g. the Trends page).
CREATE INDEX IF NOT EXISTS assessments_created_at_idx ON assessments (created_at);
