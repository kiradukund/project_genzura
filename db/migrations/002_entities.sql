-- OWNER: Abay
-- Migration 002: phone numbers, emails and links seen in scam reports.
-- Values are NEVER stored in clear: value_hash is an HMAC-SHA256 (keyed with
-- ENTITY_HASH_KEY) of "<kind>:<normalized value>", see backend/app/lookup.py.
--
-- PROPOSED columns: confirm with Chol before merging (his moderation sets `status`).

CREATE TABLE IF NOT EXISTS entities (
    id            SERIAL PRIMARY KEY,
    kind          VARCHAR(5)  NOT NULL CHECK (kind IN ('phone', 'email', 'link')),
    value_hash    CHAR(64)    NOT NULL,
    report_count  INTEGER     NOT NULL DEFAULT 0 CHECK (report_count >= 0),
    status        VARCHAR(12) NOT NULL DEFAULT 'unknown'
                  CHECK (status IN ('unknown', 'flagged', 'blacklisted')),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (kind, value_hash)
);

CREATE INDEX IF NOT EXISTS idx_entities_status ON entities (status);