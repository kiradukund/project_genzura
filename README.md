# Genzura

Anti-fraud tool that helps young people in Rwanda check overseas job, scholarship and visa offers before they pay.
Flask backend, PostgreSQL database, React (Vite) frontend.

**Live demo:** https://genzura-web.onrender.com
**API:** https://genzura-api-f40h.onrender.com (`/health`)

The free API sleeps when idle, so the first request can take about a minute.

## Features

| Feature | Status |
|---|---|
| Scam check API (`POST /api/check`): weighted rule engine, English + Kinyarwanda rules | Done |
| Personal data masking (email, phone, names) before anything is stored | Done |
| Checks saved to PostgreSQL | Done |
| Website: home page, checker, sample scams, risk result, share on WhatsApp, Report to RIB (166) | Done |
| Screenshot reading (OCR) in the browser, image never uploaded | Done |
| English / Kinyarwanda language switch | Done |
| Official Verification Directory (20 institutions) | Done |
| USSD / SMS message texts (EN + RW, feature-phone safe) | Done |
| Live deployment (Render + Neon PostgreSQL), auto-deploy on every merge into dev | Done |
| Link checker, entity lookup, report + moderation, guided assessment, "Already paid?" guide | In progress |
| Admin login + dashboard, trending scams, user accounts | In progress |
| USSD, SMS, WhatsApp bot, scam alerts (Africa's Talking / WhatsApp) | Next |
| Licensed-agency registry, email classification, file checks, partner API | Planned |

## Team

| Name | Role | ALU email | GitHub |
|---|---|---|---|
| Kevin Iradukunda Cyusa | Project Manager / Team Lead | k.iradukund@alustudent.com | kiradukund |
| Abay Mulat Tessema | Lead Backend: rule engine, API | a.tessema@alustudent.com | abay-tessema |
| Chol Mach Kuol Chol | Database Architect: schema, PII redaction | c.chol1@alustudent.com | Chol-Mach-Kuol |
| Kuol Akech Riak Kuol | Frontend lead & channels (USSD, SMS, alerts) | k.kuol@alustudent.com | k-kuol |
| Alier Akuang Alier | Kinyarwanda, USSD/SMS texts, guided assessment, UI design lead | a.piel@alustudent.com | apiel-max |
| Didier Abizera | Verification Directory, admin dashboard | d.abizera@alustudent.com | didier-abizera |

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

Create a database and load the schema:

    createdb genzura
    psql -d genzura -f db/schema.sql

Create `backend/.env` (never commit it):

    DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/genzura

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

99 tests: rule engine, PII redaction, `/api/check`, USSD/SMS message limits.

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

How a check works: the rules run on the raw text, then the text is masked (`[EMAIL]`, `[PHONE]`, `[NAME]`), and only the masked copy is stored.

## Git workflow

- Never push directly to `main`.
- Branch from `dev`: `git checkout dev`, `git pull origin dev`, `git checkout -b feature/short-task-name`
- Commit, push your branch, and open a pull request into `dev`.
- The Project Manager reviews, tests and merges into `dev`, and merges `dev` into `main` when `dev` is stable.
- Never commit `.env` files or secrets.

## Deployment

Genzura runs on Render (`render.yaml`) with a Neon PostgreSQL database.

- `genzura-api`: Flask + gunicorn (Python 3.12), health check `/health`, env var `DATABASE_URL`
- `genzura-web`: static React build, env var `VITE_API_URL` (the API address, set at build time)
- Both deploy automatically on every merge into `dev`.
- New files in `db/migrations/` are run on the live database by the Project Manager after merge.
- Secrets live only in Render's environment settings, never in the repo. See `backend/.env.example` and `frontend/.env.example`.