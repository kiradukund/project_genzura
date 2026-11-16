-- OWNER: Kuol - alert subscriptions: delete numbers on unsubscribe
-- Run once on Neon after this PR is merged.
--
-- Unsubscribing (form or reply STOP) now deletes the row instead of setting
-- active = FALSE, so we keep no phone number once someone says stop
-- (right to erasure, Law N° 058/2021; see docs/data-protection.md).
--
-- 1. Delete the numbers of people who already unsubscribed.
-- 2. Drop unsubscribed_at, which is no longer used.
-- The active column stays for now: the weekly send still filters on it,
-- so nothing breaks if the code is deployed before this file is run.

DELETE FROM alert_subscribers WHERE NOT active;

ALTER TABLE alert_subscribers DROP COLUMN IF EXISTS unsubscribed_at;
