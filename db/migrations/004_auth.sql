-- OWNER: Abay
-- Migration 004: phone + SMS-code accounts.
-- Phone numbers are NEVER stored: phone_hash is an HMAC-SHA256 keyed with
-- PHONE_HASH_KEY (a different key from the entities table, so the two cannot
-- be linked). admin_users already exists in schema.sql and is unchanged.

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    phone_hash    CHAR(64)    NOT NULL UNIQUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS sms_codes (
    id          SERIAL PRIMARY KEY,
    phone_hash  CHAR(64)    NOT NULL,
    code_hash   CHAR(64)    NOT NULL,   -- keyed hash of the 6-digit code, never the code
    attempts    INTEGER     NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    expires_at  TIMESTAMPTZ NOT NULL,   -- created_at + 5 minutes
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Serves both "newest live code" and "requests in the last hour".
CREATE INDEX IF NOT EXISTS idx_sms_codes_phone_created ON sms_codes (phone_hash, created_at);

-- "My checks": a signed-in user's checks. Deleting the account deletes them.
ALTER TABLE checks
    ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_checks_user_id ON checks (user_id);