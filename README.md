\# Genzura



Anti-fraud tool that helps job-seekers verify overseas job, scholarship, and visa offers.

Flask backend, PostgreSQL database, React (Vite) frontend.



\## Project structure



```

backend/    Flask API (app/, tests/, wsgi.py)

db/         PostgreSQL schema (schema.sql)

frontend/   React + Vite app

```



\## Prerequisites



\- Python 3.11+

\- Node.js 20+

\- Git



\## Run the backend



Windows (CMD):



```cmd

cd backend

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

python wsgi.py

```



Mac/Linux:



```bash

cd backend

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

python wsgi.py

```



API runs at http://localhost:5000. Check http://localhost:5000/health.



\## Run the tests



With the venv active, from `backend/`:



```

pytest

```



\## Run the frontend



```

cd frontend

npm install

npm run dev

```



App runs at http://localhost:5173 and proxies `/api` and `/health` to the backend.



\## API



`POST /api/check`



Request:



```json

{ "text": "message to check", "context": "job" }

```



`context` is one of `job`, `scholarship`, `visa`.



Response:



```json

{ "risk\_score": 75, "verdict": "high\_risk", "flags": \["upfront\_fee"] }

```



\## Git workflow



\- Never push directly to `main`.

\- Branch from `dev`: `git checkout dev`, `git pull origin dev`, `git checkout -b feature/short-task-name`

\- Commit, push your branch, and open a pull request into `dev`.

\- The Project Manager merges `dev` into `main` when `dev` is stable.

\- Never commit `.env` files or secrets.

