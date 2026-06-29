# Personal Finance Dashboard

Personal Finance Dashboard is a full-stack portfolio/demo project for tracking expenses, budgets, dashboard analytics, stock watchlists, AI-assisted summaries, and monthly report exports.

The current stable version is intended for local demo use: it should start from VS Code F5 on Windows, pass backend/frontend tests, build the frontend, and keep API contracts aligned across FastAPI and Vue.

## Project Status

This repository is a portfolio/demo project prepared for a v1.0 demo-ready milestone.

Implemented demo surface:

- FastAPI backend
- Vue frontend
- Auth with access token, refresh token, and logout revoke flow
- Dashboard analytics
- Budget management and budget health summaries
- Stock watchlist
- Monthly reports
- AI-assisted finance summary
- CSV and PDF export

Demo readiness already in place:

- Backend tests
- Frontend tests
- GitHub Actions CI
- VS Code F5 full-stack startup on Windows

## Features

- Expense and income tracking
- Monthly budget setup and budget health summaries
- Dashboard cards, charts, recent transactions, and report export
- Stock watchlist with cached market data, sync status, fundamentals screening, and per-item currency display
- AI finance summary and budget advice with deterministic fallback behavior
- CSV and PDF monthly report export
- Demo auth with access tokens, refresh tokens, and logout refresh-token revoke flow

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic, SQLite, pytest
- Frontend: Vue 3, Pinia, Vue Router, vue-i18n, Axios, Vite, Vitest
- Development: VS Code launch/tasks, PowerShell scripts for Windows, optional shell script for macOS/Linux

## Environment Setup

Copy the local environment examples before running the app:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Useful default URLs:

- Backend API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Frontend: `http://127.0.0.1:5173`

## Backend Start

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

For an existing environment, rerun the install and migration commands after dependency or migration changes.

## Frontend Start

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

The frontend dev server proxies `/api` requests to `http://127.0.0.1:8000`.

## VS Code F5 Start

Windows is the supported F5 path for this stable demo version.

1. Open the repository root in VS Code.
2. Install the VS Code Python and JavaScript debugging extensions if prompted.
3. Select `Full Stack Dev (F5)` in Run and Debug.
4. Press F5.

The F5 compound launch runs:

- `dev: prepare`: runs the backend/frontend bootstrap steps, including creating `backend\.venv` if missing, installing backend requirements, running Alembic migrations, and running frontend `npm ci`
- `Backend API (FastAPI)`: starts Uvicorn from `backend\.venv\Scripts\python.exe`
- `Frontend Dev Server`: starts Vite from the `frontend` working directory

Current local URLs:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

macOS/Linux users can run the app manually with the commands above or use:

```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

The shell script is provided for convenience, but the VS Code F5 workflow is currently documented and verified for Windows.

## One-Click Windows Script

From the repository root:

```powershell
.\start-dev.bat
```

Or run the PowerShell script directly:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\start-dev.ps1
```

The script checks Python, Node.js, and npm, prepares dependencies, applies migrations, and opens separate backend/frontend dev-server windows.

## Tests

Backend:

```powershell
cd backend
python -m compileall .
python -m pytest -q
```

Frontend:

```powershell
cd frontend
npm ci
npm run lint
npm run test:run
npm run build
npm audit --audit-level=moderate
```

## Monthly Report Export

The Dashboard page can export monthly reports as CSV or PDF.

Backend endpoints:

- `GET /api/reports/monthly?month=YYYY-MM&format=csv`
- `GET /api/reports/monthly?month=YYYY-MM&format=pdf`

Rules:

- Authentication is required
- Exported data is scoped to the current user
- `month` must use `YYYY-MM`
- `format` supports `csv` and `pdf`
- Empty months still return a valid empty report

## Demo Security Model

This is a portfolio/demo project, not a finished production security baseline.

Implemented demo-level security behavior includes:

- Password hashing
- JWT access tokens
- Refresh tokens
- Refresh-token rotation
- Logout revoke flow for refresh tokens
- User-scoped queries for expenses, budgets, reports, dashboard data, and watchlists
- Development guard that requires a real `SECRET_KEY` when `ENV=production`

For production, the project should still add or harden:

- Shorter access token lifetime than the current demo default
- HttpOnly Secure Cookie storage for tokens
- CSP and other security headers
- Production secret management
- Centralized/rate-limited auth protection
- HTTPS-only deployment configuration
- Stronger observability and incident logging

Do not treat the current token/local-storage model as production-grade security.

## Known Limitations / Roadmap

- Transaction editing is not implemented yet.
- Recurring transactions are not implemented yet.
- Bank CSV import is not implemented yet.
- Stock functionality is a watchlist, not a full portfolio profit/loss system.
- PDF report labels are currently mostly English to avoid Chinese font environment issues.

## Common Issues

- Missing Python packages: run `backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`.
- Missing frontend packages: run `npm ci` in `frontend`.
- Alembic or SQLite state looks stale: from `backend`, run `.\.venv\Scripts\python.exe -m alembic upgrade head`.
- Port already in use: stop the existing process on ports `8000` or `5173`, or change the launch/script port arguments.
- OpenAI key missing: AI endpoints degrade to deterministic fallback text unless a real provider and key are configured.
- `npm audit` reports issues after dependency updates: inspect the vulnerable package path first and prefer compatible patch/minor upgrades before major upgrades.

## CI

GitHub Actions runs:

- backend import smoke
- backend Alembic migration smoke
- backend `python -m compileall .`
- backend `python -m pytest -q`
- frontend `npm ci`
- frontend lint
- frontend tests
- frontend build

Workflow file:

- [.github/workflows/ci.yml](.github/workflows/ci.yml)
