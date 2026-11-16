# Genzura

Anti-fraud tool that helps young people in Rwanda check overseas job, scholarship and visa offers before they pay.
Flask backend, PostgreSQL database, React (Vite) frontend.

**Live demo:** https://genzura-web.onrender.com
**API:** https://genzura-api-f40h.onrender.com (`/health`)

The free API sleeps when idle, so the first request can take about a minute.

## Features

| Feature | Status |
|---|---|
| Scam check (`POST /api/check`): weighted rule engine, English + Kinyarwanda rules, known scam contacts flagged | Done |
| Personal data masking (email, phone, names) before anything is stored | Done |
| Screenshot reading (OCR) in the browser, image never uploaded | Done |
| Guided assessment: 6 questions, risk level with reasons | Done |
| Report a scam, admin review queue (approve/reject), audit log | Done |
| Scam-contact lookup (phones, emails, links stored only as hashes) | Done |
| Admin dashboard: real statistics, admin login | Done |
| Phone sign-in (SMS code) and "My checks" history, account deletion | Done (SMS via Africa's Talking sandbox) |
| Agency check: no agency is licensed for jobs abroad yet, with sources | Done |
| "Already paid?" guide, Official Verification Directory, redesign, full Kinyarwanda | Done |
| Partner API (`POST /v1/check`): API keys, daily limits | Done |
| WhatsApp bot (webhook, signature check) | Built, needs a WhatsApp Business number to go live |
| USSD, SMS results, scam alerts | In progress |
| Trending scams page | In progress |
| Link checks: short links, spam endings, fake government and look-alike sites (`irembo-gov.com`) | Done |
| Domain trust: follows short links, flags websites registered in the last 90 days | Done (web and WhatsApp checks) |
| PDF offer letters read in the browser (text and scanned), file never uploaded | Done |
| Email classification (disposable addresses, external APIs), QR codes | Cut (out of scope) |

## Team

| Name | Role | ALU email | GitHub |
|---|---|---|---|
| Kevin Iradukunda Cyusa | Project Manager / Team Lead, Partner API, deployment | k.iradukund@alustudent.com | kiradukund |
| Abay Mulat Tessema | Lead Backend: rule engine, API, login, scam-contact lookup | a.tessema@alustudent.com | abay-tessema |
| Chol Mach Kuol Chol | Database Architect: schema, PII redaction, reports + moderation, link checks | c.chol1@alustudent.com | Chol-Mach-Kuol |
| Kuol Akech Riak Kuol | Frontend lead & channels (USSD, SMS, alerts) | k.kuol@alustudent.com | k-kuol |
| Alier Akuang Alier | Kinyarwanda, USSD/SMS texts, guided assessment, trending scams | a.piel@alustudent.com | apiel-max |
| Didier Abizera | Verification Directory, admin dashboard, agency check, WhatsApp bot | d.abizera@alustudent.com | didier-abizera |

## Project structure

    backend/app/       Flask API: one file per feature (blueprint), each with an OWNER line
    backend/tests/     One test file per feature
    db/schema.sql      Base schema (do not edit)
    db/migrations/     Numbered SQL files, one per feature owner
    frontend/src/      React + Vite app (pages/, components/, api/, i18n/)
    render.yaml        Deployment config (Render)
    .github/CODEOWNERS Who reviews which file

## Who owns what

Every feature file starts with an `OWNER` line. Only edit files with your name on them;
`.github/CODEOWNERS` asks the owner to review any change to their files.

- Text: add English inside your own block in `frontend/src/i18n/en.json`. Only Alier edits `rw.json`.
- Database: add tables only in your numbered file in `db/migrations/`. Never edit `db/schema.sql`, `db.py` or `__init__.py`.
- Navigation: only Kuol edits `App.jsx`, `Header.jsx`, `Home.jsx` and `styles.css`.

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- Git

## Set up the database

Create a database, load the schema, then every migration in order:

    createdb genzura
    psql -d genzura -f db/schema.sql
    for f in db/migrations/*.sql; do psql -d genzura -f "$f"; done

(Windows: run `psql -d genzura -f db\migrations\002_entities.sql` and so on, one file at a time.)

Create `backend/.env` (never commit it):

    DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/genzura
    SECRET_KEY=any-long-random-text
    PHONE_HASH_KEY=any-long-random-text
    ENTITY_HASH_KEY=any-long-random-text
    COOKIE_SECURE=false

Generate the random values with `python -c "import secrets; print(secrets.token_hex(32))"`.
`COOKIE_SECURE=false` is only for local `http://`; never set it on Render.

Without a database the API still scores messages, but returns `"check_id": null` and saves nothing.

## Run the backend

Windows (CMD):

    cd backend
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python wsgi.py

Mac/Linux:

    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python wsgi.py

API runs at http://localhost:5000. Check http://localhost:5000/health.

## Run the tests

With the venv active, from `backend/`:

    pytest

298 tests, one file per feature. All must pass before a pull request is opened.

## Run the frontend

    cd frontend
    npm install
    npm run dev

App runs at http://localhost:5173 and forwards `/api` and `/health` to the backend.
In production, set `VITE_API_URL` to the backend address.

## API

`POST /api/check`

Request:

    { "text": "message to check", "context": "job", "language": "en" }

- `context`: `job`, `scholarship` or `visa` (default `job`)
- `language`: `en` or `rw` (default `en`)

Response `200`:

    { "risk_score": 75, "verdict": "high_risk", "flags": ["upfront_fee", "guaranteed_outcome"], "check_id": 12 }

- `verdict`: `low_risk`, `suspicious` or `high_risk`
- `check_id` is `null` if the check could not be saved

Response `400`: `{ "error": "text is required" }` (also for an invalid `context` or `language`).

### All endpoints

| Method | Path | Who | What |
|---|---|---|---|
| `GET` | `/health` | Anyone | Is the API running |
| `POST` | `/api/check` | Anyone | Check a message |
| `POST` | `/api/lookup` | Anyone | Are these phones/emails/links reported as scams |
| `GET` | `/api/assess/questions` | Anyone | Guided assessment questions |
| `POST` | `/api/assess` | Anyone | Score the answers |
| `POST` | `/api/reports` | Anyone | Report a scam |
| `GET` | `/api/agencies` | Anyone | Licensed agencies (none yet) and official contacts |
| `POST` | `/api/auth/phone/request` | Anyone | Send a sign-in code by SMS |
| `POST` | `/api/auth/phone/verify` | Anyone | Check the code and sign in |
| `GET` | `/api/auth/me` | Signed in | Who am I |
| `GET` | `/api/me/checks` | User | My check history |
| `DELETE` | `/api/auth/account` | User | Delete my account and my history |
| `POST` | `/api/auth/logout` | Signed in | Sign out |
| `POST` | `/api/auth/admin/login` | Team | Admin sign-in (email + password) |
| `GET` | `/api/admin/stats` | Admin | Dashboard statistics |
| `GET` | `/api/admin/reports` | Admin | Report queue (`?status=pending`) |
| `POST` | `/api/admin/reports/<id>/approve` | Admin | Approve a report |
| `POST` | `/api/admin/reports/<id>/reject` | Admin | Reject a report |
| `GET`/`POST` | `/api/whatsapp` | WhatsApp | Webhook (verify / receive) |
| `POST` | `/v1/check` | Partners | Partner API (needs `X-API-Key`) |

Bad input returns `400`, a missing or wrong login `401`, and an unavailable database `503`.

How a check works: the rules run on the raw text, then the text is masked (`[EMAIL]`, `[PHONE]`, `[NAME]`), and only the masked copy is stored.

### Partner API

`POST /v1/check` lets partner organizations (job boards, NGOs, scholarship offices) check messages from their own systems.
It needs an API key in the `X-API-Key` header.

    curl -X POST https://genzura-api-f40h.onrender.com/v1/check \
      -H "Content-Type: application/json" \
      -H "X-API-Key: YOUR_KEY" \
      -d '{"text": "Guaranteed visa, pay the processing fee now", "context": "visa"}'

Request body: same as `/api/check`. `text` must be at most 2000 characters.

Response `200`: same as `/api/check`, plus `requests_remaining_today`.

    { "risk_score": 60, "verdict": "high_risk", "flags": ["upfront_fee", "guaranteed_outcome"], "check_id": 2, "requests_remaining_today": 999 }

| Status | Meaning |
|---|---|
| `400` | Invalid input (missing or non-text `text`, too long, bad `context` or `language`) |
| `401` | Missing or invalid API key |
| `429` | Daily limit reached (default 1000 requests per key, resets each day) |
| `503` | Database unavailable; the key cannot be verified, so the request is refused |

Partner checks are saved with `channel = 'api'`.

Managing keys (Project Manager only):

- Create: from `backend/`, with `DATABASE_URL` set, run `python create_api_key.py "Partner name"` (optional daily limit: `python create_api_key.py "Partner name" 500`).
  The key is printed once. Only its SHA-256 hash is stored, so a lost key cannot be recovered, only replaced.
- Disable: `UPDATE api_keys SET active = false WHERE id = <id>;`

## Admin accounts

There is no sign-up page for admins. The Project Manager creates them from `backend/`
(venv active, `DATABASE_URL` pointing to the database):

    python create_admin.py someone@alustudent.com            (role: admin)
    python create_admin.py someone@alustudent.com reviewer   (role: reviewer)

The password is typed twice and never shown, must be at least 10 characters, and only its hash
is stored. Running the command again for the same email sets a new password.
Both roles currently have the same access.

## Git workflow

- Never push directly to `main`.
- Branch from `dev`: `git checkout dev`, `git pull origin dev`, `git checkout -b feature/short-task-name`
- Commit, push your branch, and open a pull request into `dev`.
- Never merge your own pull request: `dev` and `main` need 1 approval.
- The Project Manager reviews, tests and merges into `dev`, and merges `dev` into `main` when `dev` is stable.
- Never commit `.env` files or secrets.

## Deployment

Genzura runs on Render (`render.yaml`) with a Neon PostgreSQL database.

- `genzura-api`: Flask + gunicorn (Python 3.12), health check `/health`
- `genzura-web`: static React build
- Both deploy automatically on every merge into `dev`.
- New files in `db/migrations/` are run on the live database by the Project Manager after merge.
- Secrets live only in Render's environment settings, never in the repo.

Environment variables on Render (`genzura-api`):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Neon connection string |
| `PYTHON_VERSION` | `3.12.7` |
| `SECRET_KEY` | Signs login cookies |
| `PHONE_HASH_KEY` | Hashes phone numbers. Never change it once users exist |
| `ENTITY_HASH_KEY` | Hashes reported phones/emails/links. Never change it once reports exist |
| `COOKIE_SAMESITE` | `None`, so the login cookie works between the site and the API |
| `FRONTEND_ORIGINS` | Optional: sites allowed to send login cookies (default: localhost + genzura-web) |
| `AT_USERNAME`, `AT_API_KEY` | Africa's Talking (`sandbox` for now): SMS codes, USSD |
| `DOMAIN_CHECKS_ONLINE` | Optional: `false` turns off the online link checks (redirects, domain age) |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN` | WhatsApp bot (not set yet, so the bot is off) |

`genzura-web` needs `VITE_API_URL` (the API address, set at build time).

Migrations run on the live database: 002, 003, 004, 005, 007.
