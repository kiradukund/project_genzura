## Contents

- [Features](#features)
- [Team](#team)
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Who owns what](#who-owns-what)
- [Prerequisites](#prerequisites)
- [Set up the database](#set-up-the-database)
- [Run the backend](#run-the-backend)
- [Run the tests](#run-the-tests)
- [Run the frontend](#run-the-frontend)
- [API](#api)
  - [All endpoints](#all-endpoints)
  - [Partner API](#partner-api)
- [Admin accounts](#admin-accounts)
- [Git workflow](#git-workflow)
- [Deployment](#deployment)
- [Known limitations](#known-limitations)
  
# Genzura

Anti-fraud tool that helps young people in Rwanda check overseas job, scholarship and visa offers before they pay.
Flask backend, PostgreSQL database, React (Vite) frontend.

**Live demo:** https://genzura-web.onrender.com
**API:** https://genzura-api-f40h.onrender.com/health (health check; the API itself has no home page)

The free API sleeps when idle, so the first request can take about a minute.

| Home | A real check result | Phone |
|---|---|---|
| ![Home page](docs/screenshots/home.jpg) | ![HIGH RISK result with the red flags found](docs/screenshots/check-result.png) | ![Home page on a phone](docs/screenshots/mobile.jpg) |

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
| USSD menu, "send result to my phone" SMS, weekly scam alerts by SMS | Built and tested; live only in the Africa's Talking sandbox (a real shortcode needs a paid account) |
| Trending scams page: most common red flags of the last 7 / 30 days (counts only) | Done |
| Privacy page (what is kept, for how long, who processes it) | Done |
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

## How it works

```mermaid
flowchart LR
    U["Web browser<br/>(React + Vite)"] -->|HTTPS + login cookie| API
    P["Feature phone<br/>USSD / SMS"] -->|Africa's Talking| API
    W["WhatsApp"] -->|Meta webhook| API
    X["Partner systems"] -->|X-API-Key| API

    subgraph API["Flask API (genzura-api on Render)"]
        R["rules.py<br/>weighted rules, EN + RW"] --> L["links.py + domains.py<br/>link and look-alike site checks"]
        L --> K["lookup.py<br/>reported scam contacts"]
        K --> M["redaction<br/>mask emails, phones, names"]
    end

    M -->|masked text + result only| DB[("PostgreSQL<br/>Neon")]
    API -->|SMS codes, results, alerts| AT["Africa's Talking"]
    L -.->|online: redirects, domain age| NET["Internet (RDAP)"]
```

1. A message comes in from the website, USSD, SMS, WhatsApp or a partner.
2. The rule engine scores it (0 to 100) and lists the red flags. Links are checked offline
   (short links, spam endings, sites copying official names such as `irembo-gov.com`) and, for web
   and WhatsApp checks, online (where a short link really leads, how old the website is).
3. Phones, emails and links are compared with approved scam reports, which are stored only as hashes.
4. Personal details are masked, and only the masked copy and the result are saved.
5. The user gets a verdict (low risk, suspicious, high risk), the reasons, and what to do next.

Screenshots and PDF letters are read inside the browser; the files are never uploaded.

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

502 tests, one file per feature. All must pass before a pull request is opened.

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
| `GET` | `/api/trends` | Anyone | Most common red flags (`?days=7` or `30`), counts only |
| `POST` | `/api/send-result` | Anyone | Text the result of a recent check to a phone |
| `POST` | `/api/alerts/subscribe` | Anyone | Sign up for weekly scam alerts by SMS |
| `POST` | `/api/alerts/unsubscribe` | Anyone | Stop alerts (the number is deleted) |
| `POST` | `/api/alerts/send-weekly` | Scheduler | Send the weekly alert (needs `X-Cron-Token`) |
| `POST` | `/api/ussd` | Africa's Talking | USSD menu (EN/RW) |
| `POST` | `/api/sms/inbound` | Africa's Talking | Incoming SMS: check a message, STOP |
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
| `ALERTS_CRON_TOKEN` | Optional: turns on `/api/alerts/send-weekly` (not set yet) |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN` | WhatsApp bot (not set yet, so the bot is off) |

`genzura-web` needs `VITE_API_URL` (the API address, set at build time).

Migrations run on the live database: 002 to 007 and 009 (008 has no tables).

## Known limitations

- **SMS and USSD** use the Africa's Talking sandbox: codes and results reach only the AT simulator, not real phones, until a paid account and shortcode are set up.
- **WhatsApp bot** is built and tested but off: it needs a WhatsApp Business number from Meta.
- **Data location:** the database is hosted by Neon in the United States. Rwanda's data protection law (Law 058/2021, Article 50) requires an NCSA certificate to store personal data abroad; a Rwandan host would remove this issue.
- **Rules, not machine learning:** checks follow written rules, so a new kind of scam is missed until a rule is added. Approved reports help catch repeat scammers.
- **Free hosting** sleeps when idle (about a minute for the first request).
- **Login on Safari** may fail, because Safari blocks cookies between the site and the API on different domains.
