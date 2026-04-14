# Personal Finance Dashboard v0.6.1

Personal Finance Dashboard is a demo full-stack project built with FastAPI, SQLAlchemy, Vue 3, Pinia, and Vite. This version is stabilized around four goals:

- `npm run build` passes on the frontend.
- Backend and frontend contracts are consistent.
- SQLite delivery is reproducible through clean init and seed steps.
- Budget and stock status logic is defined in one place and rendered consistently in the UI.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- Frontend: Vue 3, Pinia, Vue Router, Vite
- Python: recommended `3.11` or `3.12`
- Node.js: recommended `18` or newer

## Version Contract

The following version markers are intentionally aligned to `0.6.1`:

- README version
- FastAPI app version
- Frontend package version
- Frontend UI version display

## Demo Account

- Email: `demo@example.com`
- Password: `demo1234`

## Environment Setup

1. Copy the example env file at the repository root.
2. Fill in `SECRET_KEY` if you want a non-default development key.

Example:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Root `.env.example` includes:

```env
ENV=development
SECRET_KEY=
CORS_ORIGINS=http://localhost:5173
DATABASE_URL=sqlite:///./finance.db
```

## From Scratch

### 1. Install backend dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

### 2. Initialize a clean database and seed demo data

This project does not rely on an old committed `finance.db`. Use the seed script to create a fresh SQLite database and demo records:

```bash
python seed_data.py --reset
```

Optional (for long-term demos): shift the deterministic dataset to recent months while preserving record shapes:

```bash
python seed_data.py --reset --relative-dates
```

This creates:

- the SQLite schema
- the demo user
- demo expenses
- demo budgets
- demo watchlist items
- demo stock prices

### 3. Start the backend

```bash
uvicorn main:app --reload
```

Backend default URL:

- API root: [http://localhost:8000](http://localhost:8000)
- Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Install frontend dependencies

```bash
cd ../frontend
npm install
```

### 5. Start the frontend

```bash
npm run dev
```

Frontend default URL:

- App: [http://localhost:5173](http://localhost:5173)

## Build

Frontend production build:

```bash
cd frontend
npm install
npm run build
```

`npm install` is required for official verification. Do not treat archived or copied `node_modules` folders as a valid build source.

Frontend lint:

```bash
cd frontend
npm run lint
```

## Testing

Backend smoke tests:

```bash
cd backend
python -m pytest
```

Current smoke coverage includes:

- auth: register / login / me
- expenses: create / list / delete
- budgets: create / list / delete
- dashboard summary
- user isolation for authenticated resources

## Stable Data Rules

### Budget summary

All current-month budget calculations follow the same rules:

- `date >= month_start`
- `date < next_month_start`
- `type == "expense"`

This logic is centralized in `backend/services/budget_summary.py` and reused by:

- `backend/routers/budgets.py`
- `backend/routers/dashboard.py`
- `backend/routers/ai.py`

### SQLite delivery

- `backend/finance.db` is ignored and should not be committed as a delivery artifact.
- `python seed_data.py --reset` is the supported reproducible reset path.
- Relative SQLite paths are normalized against the `backend` directory so the database location does not drift with the current shell working directory.
- The app initializes tables for a clean database and fails fast if an existing SQLite file is missing required tables, instead of silently patching an old schema in place.
- Local database files are runtime artifacts, not release validation artifacts.

### Frontend dependency lock

- `frontend/package-lock.json` is the single source of truth for dependency versions.
- `frontend/node_modules` is a local install artifact and must not be treated as release evidence.
- Use `cd frontend && npm install && npm run build` for reproducible verification.

### Stock watchlist sync status

Watchlist rows expose exactly three sync states:

- `success`
- `pending`
- `failed`

Frontend rendering matches these states directly from backend response fields. Failed sync status is persisted per watchlist item together with the latest sync error, so add-to-watchlist feedback and later refreshes stay consistent.

### Mock stock screening scope

Fundamental screening is still mock-based for a limited set of bundled symbols. The UI explicitly states that screening coverage is only available for that mock list so users do not mistake it for full live market analysis.

## Known Limits

- SQLite is suitable for demo and local use, but this project does not yet include Alembic migrations.
- Stock prices depend on `yfinance`; transient upstream failures can still produce `failed` sync states.
- Fundamental screening remains mock-backed rather than fully live.
- `.env` loading is included for local development, but production deployment still needs explicit secret and environment management.
- The default seed dataset uses fixed reference dates for deterministic demos. Use `--relative-dates` when you want the same dataset shape mapped to recent months.

## Packaging and Cleanup

Run cleanup before packaging to avoid shipping local artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/clean-delivery.ps1
```

This removes local artifacts such as:

- `backend/finance.db`
- `backend/test_smoke.db`
- `backend/__pycache__`
- `backend/.pytest_cache`
- `frontend/node_modules`
- `frontend/dist`
- `frontend/.vite`

For source-only delivery that excludes `.git`, use:

```bash
git archive --format zip --output personal-finance-dashboard.zip HEAD
```

## Release Checklist

- Run `python seed_data.py --reset` inside `backend`.
- Run `python -m pytest` inside `backend`.
- Run `npm install && npm run lint && npm run build` inside `frontend`.
- Confirm the UI can sign in with `demo@example.com / demo1234`.
- Confirm dashboard, expenses, budgets, and stocks pages load without console or API contract errors.
