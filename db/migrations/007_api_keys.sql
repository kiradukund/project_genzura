-- OWNER: Kevin - partner api_keys
-- Run once on Neon after this PR is merged.

CREATE TABLE IF NOT EXISTS api_keys (
    id              SERIAL PRIMARY KEY,
    partner_name    VARCHAR(200) NOT NULL,
    key_prefix      VARCHAR(16)  NOT NULL,
    key_hash        CHAR(64)     NOT NULL UNIQUE,
    daily_limit     INTEGER      NOT NULL DEFAULT 1000 CHECK (daily_limit > 0),
    requests_today  INTEGER      NOT NULL DEFAULT 0,
    usage_date      DATE         NOT NULL DEFAULT CURRENT_DATE,
    active          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_used_at    TIMESTAMPTZ
);

-- Partner checks are saved with channel 'api'. 'whatsapp' is added here too
-- so Didier's WhatsApp bot does not need a second migration on the same rule.
ALTER TABLE checks DROP CONSTRAINT IF EXISTS checks_channel_check;
ALTER TABLE checks ADD CONSTRAINT checks_channel_check
    CHECK (channel IN ('web', 'ussd', 'sms', 'whatsapp', 'api'));
