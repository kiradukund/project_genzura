# Genzura

Anti-fraud tool that helps young people in Rwanda check overseas job, scholarship and visa offers before they pay.
Flask backend, PostgreSQL database, React (Vite) frontend.

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
| USSD and SMS channels (Africa's Talking) | Next |
| Report a scam, verify an agency, admin dashboard | Next |

## Team

| Name | Role | ALU email | GitHub |
|---|---|---|---|
| Kevin Iradukunda Cyusa | Project Manager / Team Lead | k.iradukund@alustudent.com | kiradukund |
| Abay Mulat Tessema | Lead Backend: rule engine, API | a.tessema@alustudent.com | abay-tessema |
| Chol Mach Kuol Chol | Database Architect: schema, PII redaction | c.chol1@alustudent.com | Chol-Mach-Kuol |
| Kuol Akech Riak Kuol | Frontend & SMS | k.kuol@alustudent.com | k-kuol |
| Alier Akuang Alier | Kinyarwanda translations, USSD/SMS texts | a.piel@alustudent.com | apiel-max |
| Didier Abizera | Verification Directory, admin dashboard | d.abizera@alustudent.com | didier-abizera |

## Project structure

    backend/    Flask API (app/, tests/, wsgi.py)
    db/         PostgreSQL schema (schema.sql)
    frontend/   React + Vite app

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
