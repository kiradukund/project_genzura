# Data protection

Owner: Didier · Checked: 16 Nov 2026 · Student research, not legal advice.

Genzura handles personal data (phone numbers, message text), so Rwanda's
**Law N° 058/2021 on the protection of personal data and privacy** applies.
It is enforced by the National Cyber Security Authority (NCSA).

## The law in short

- **Consent:** freely given, specific, informed and clear; can be withdrawn.
- **Rights:** people can ask to access, correct or **erase** their data.
- **Registration:** organisations processing personal data register with NCSA.
- **Storage:** personal data must be stored in Rwanda unless NCSA authorises otherwise.
- **Breaches:** tell NCSA within 48 hours, full report within 72 hours.

## What Genzura stores

| Data | How it is stored |
| --- | --- |
| Checked messages (`checks`) | Masked text only (`[PHONE]`, `[EMAIL]`, `[NAME]`), verdict, flags, channel |
| User accounts (`users`) | Phone as a keyed hash (HMAC-SHA256), never the real number |
| Sign-in codes (`otp_codes`) | Hashed, expire after 5 minutes |
| Admin accounts (`admin_users`) | Email + password hash |
| Scam reports | Masked text and contact |
| Partner API keys | SHA-256 hash only |
| WhatsApp sender | Used to reply, never stored or logged |
| Alert subscribers (`alert_subscribers`) | **Real phone number** (needed to send alerts) |
| Admin dashboard | Aggregated figures only, no personal data |

Users can delete their account, checks and codes: `DELETE /api/auth/account`.

## Pilot rules

The pilot uses **test data only**: team phone numbers and provider sandboxes,
no public users.

## Known limitations

1. **Hosting abroad.** Neon (database) and Render (API, website) are outside
   Rwanda. We keep data minimal (hashed phones, masked text) and say this
   openly. Kevin is checking with our facilitator.
2. **Alert subscribers.** `alert_subscribers` keeps real numbers, and
   unsubscribing only sets `active = FALSE`. Proposal (Kuol): delete or
   anonymise the number on unsubscribe.
3. **Consent wording.** Sign-in, alerts and WhatsApp should say in one line
   what we store and why (Alier for EN/RW texts).

## Before any public launch

- [ ] NCSA registration certificate, **or** move hosting to a Rwanda-based provider
- [ ] Consent line on sign-in, alerts and the first WhatsApp reply
- [ ] Delete alert numbers on unsubscribe
- [ ] Named breach contact and a 48-hour plan
- [ ] Decide how long checks and reports are kept

## Sources

- [DLA Piper: Data Protection in Rwanda](https://www.dlapiperdataprotection.com/index.html?c=RW&t=law)
- [Hogan Lovells: Key features of the Rwandan data protection law](https://hoganlovells.com/en/publications/key-features-of-the-new-rwandan-data-protection-law)
- [DPP Law text: obligations of controllers and processors](https://dpo.arxia.com/dpp-law/obligations-of-the-data-controller-and-the-data-processor)
- [PwC Rwanda: Why data protection goes beyond registration](https://www.pwc.com/rw/en/assets/pdf/data-protection-in-rwand.pdf)
