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
npm run build
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
- The app initializes tables for a clean database, but does not try to repair a stale schema in place.

### Stock watchlist sync status

Watchlist rows expose exactly three sync states:

- `success`
- `pending`
- `failed`

Frontend rendering matches these states directly. If a stock has no price data after loading the watchlist, it is shown as `pending`, not as a healthy synced state.

### Mock stock screening scope

Fundamental screening is still mock-based for a limited set of bundled symbols. The UI explicitly states that screening coverage is only available for that mock list so users do not mistake it for full live market analysis.

## Known Limits

- SQLite is suitable for demo and local use, but this project does not yet include Alembic migrations.
- Stock prices depend on `yfinance`; transient upstream failures can still produce `failed` sync states.
- Fundamental screening remains mock-backed rather than fully live.
- `.env` loading is included for local development, but production deployment still needs explicit secret and environment management.
