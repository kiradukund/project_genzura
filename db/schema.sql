
-- Genzura database schema (PostgreSQL)

CREATE TABLE IF NOT EXISTS checks (
    id          SERIAL PRIMARY KEY,
    channel     VARCHAR(10) NOT NULL CHECK (channel IN ('web', 'ussd', 'sms')),
    context     VARCHAR(12) NOT NULL CHECK (context IN ('job', 'scholarship', 'visa')),
    language    VARCHAR(2)  NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'rw')),
    masked_text TEXT,
    risk_score  INTEGER     NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    verdict     VARCHAR(12) NOT NULL CHECK (verdict IN ('low_risk', 'suspicious', 'high_risk')),
    flags       JSONB       NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id          SERIAL PRIMARY KEY,
    check_id    INTEGER REFERENCES checks(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    status      VARCHAR(12) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'reviewing', 'forwarded', 'closed')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verified_entities (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    type        VARCHAR(20)  NOT NULL CHECK (type IN ('employer', 'agency', 'scholarship')),
    website     VARCHAR(300),
    status      VARCHAR(12)  NOT NULL DEFAULT 'verified' CHECK (status IN ('verified', 'flagged', 'blacklisted')),
    notes       TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(200) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          VARCHAR(12) NOT NULL DEFAULT 'reviewer' CHECK (role IN ('reviewer', 'admin')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_checks_created_at ON checks (created_at);
CREATE INDEX IF NOT EXISTS idx_checks_verdict ON checks (verdict);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports (status);