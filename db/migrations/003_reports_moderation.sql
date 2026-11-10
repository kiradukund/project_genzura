-- OWNER: Chol - reports moderation and audit log

CREATE TABLE IF NOT EXISTS report_submissions (
    id           SERIAL PRIMARY KEY,
    check_id     INTEGER REFERENCES checks(id) ON DELETE SET NULL,
    masked_text  TEXT NOT NULL,
    contact      TEXT,                          -- masked phone/email of reporter
    status       VARCHAR(12) NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- When a report is approved, the phone/email/link is written to entities
-- (Abay owns entities; agree columns before inserting)
-- columns used: value TEXT, type VARCHAR, status VARCHAR default 'blacklisted'

CREATE TABLE IF NOT EXISTS audit_log (
    id           SERIAL PRIMARY KEY,
    admin_email  VARCHAR(200) NOT NULL,
    action       VARCHAR(20)  NOT NULL CHECK (action IN ('approved', 'rejected')),
    report_id    INTEGER NOT NULL REFERENCES report_submissions(id) ON DELETE CASCADE,
    note         TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_report_submissions_status ON report_submissions (status);
CREATE INDEX IF NOT EXISTS idx_audit_log_report_id ON audit_log (report_id);
