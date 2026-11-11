-- OWNER: Kuol - alert subscriptions
-- Run once on Neon after this PR is merged.
--
-- People who asked for weekly scam alerts by SMS. This is the only table that
-- keeps a phone number, because we need it to send the alert. Unsubscribing
-- (form or reply STOP) sets active = FALSE.

CREATE TABLE IF NOT EXISTS alert_subscribers (
    id              SERIAL PRIMARY KEY,
    phone           VARCHAR(16) NOT NULL UNIQUE,   -- +2507XXXXXXXX
    language        VARCHAR(2)  NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'rw')),
    active          BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    unsubscribed_at TIMESTAMPTZ,
    last_sent_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alert_subscribers_active ON alert_subscribers (active);
