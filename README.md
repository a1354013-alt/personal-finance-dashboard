# Personal Finance Dashboard

Full-stack personal finance dashboard built with FastAPI and Vue 3. The project covers budgeting, expense tracking, stock watchlists, dashboard analytics, AI summaries, and monthly report export.

## Features

- Budget management by month and category
- Expense and income tracking
- Dashboard summary with trends, category spend, budget health, and recent transactions
- Stock watchlist with cached market data and fundamentals sync jobs
- AI-generated summary and budget guidance
- Monthly report export in CSV and PDF

## Architecture

- Backend: FastAPI routers, service layer, Pydantic contracts, SQLAlchemy ORM, Alembic migrations
- Frontend: Vue 3 pages, Pinia stores, Axios API layer, contract normalizers
- Database: SQLite by default
- Background work: queued sync jobs for market data and fundamentals

## Quick Start

### Windows one-click start

From the repository root:

```powershell
.\start-dev.bat
```

PowerShell directly:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\start-dev.ps1
```

The script checks Python, Node.js, and npm, creates `backend\.venv` if needed, installs backend and frontend dependencies, runs `alembic upgrade head`, and opens separate dev-server terminals.
If `backend\.env` or `frontend\.env` is missing, the script also copies it from the matching `.env.example` file before startup.

### VS Code F5 full-stack start

Open this repository in VS Code, switch to the `Run and Debug` view, then choose `Full Stack Dev` and press `F5`.

What the bundled VS Code configuration does:

- bootstraps `backend/.venv` if it does not exist yet
- copies `backend/.env.example` or `frontend/.env.example` when the local `.env` file is still missing
- installs backend requirements and runs `alembic upgrade head`
- installs frontend packages automatically when `frontend/node_modules` is missing
- launches the FastAPI backend at `http://127.0.0.1:8000`
- launches the Vite frontend at `http://127.0.0.1:5173`

The existing `start-dev.bat` and `scripts/start-dev.ps1` flow remains supported. `F5` is just the VS Code-native entry point for the same local development workflow.

### macOS / Linux start

```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

### Environment files

The app runs with demo-safe defaults. To customize local settings:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

macOS / Linux:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Use a real `SECRET_KEY` and external API keys only in private local files or deployment secrets.

Dev URLs:

- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

## Troubleshooting

### PowerShell script cannot run

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Port already in use

Backend default: `http://localhost:8000`  
Frontend default: `http://localhost:5173`

Close the existing process or change the port before starting the dev script.

### First launch takes longer

The startup script creates `backend/.venv`, installs backend dependencies, installs frontend packages, and applies migrations on the first run.

### Database migration failed

Check `backend/.env` and `DATABASE_URL`, then rerun the startup script or `alembic upgrade head`.

## Backend Setup

```powershell
cd backend
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

Backend URLs:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Migration Commands

```powershell
cd backend
alembic upgrade head
```

If you need a clean demo database:

```powershell
cd backend
python seed_data.py --reset
```

## Reset Local Database

If an older local `finance.db` has an inconsistent `alembic_version` state, remove the local SQLite file and rebuild it from migrations and seed data.

macOS / Linux:

```bash
cd backend
rm -f finance.db
alembic upgrade head
python seed_data.py --reset
```

Windows PowerShell:

```powershell
cd backend
Remove-Item .\finance.db
alembic upgrade head
python seed_data.py --reset
```

## Demo Seed Data

```powershell
cd backend
python seed_data.py --reset
```

This creates demo data for:

- demo user
- transactions
- budgets
- stock watchlist
- cached stock prices

Demo account:

- Email: `demo@example.com`
- Password: `demo1234`

## Frontend Setup

```powershell
cd frontend
npm ci
npm run dev
```

Frontend URL:

- App: `http://localhost:5173`

## Rate Limiting

The current rate limiter is an in-memory, demo-level guard intended for a single local API process. It does not share counters across multiple workers or multiple deployed instances. Production deployments should replace it with a Redis-backed or otherwise centralized rate limiter.

## Testing Commands

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
npm run build
npm run test:run
```

## API Naming Notes

The project intentionally keeps naming strategy stable at each layer instead of forcing one naming style everywhere:

- Python services, SQLAlchemy models, and DB-oriented payloads may use `snake_case`
- Vue components, Pinia stores, and display-oriented state use `camelCase`
- Frontend contract normalizers in [frontend/src/api/contracts.js](frontend/src/api/contracts.js) are the boundary that accepts mixed API field styles and returns stable UI shapes

When extending an API response, prefer updating the response model or the matching normalizer rather than renaming every field across the stack in one pass.

## Monthly Report Export

Monthly report export is available from both backend API and the Dashboard page.

As a portfolio feature, this export turns the Dashboard from a screen-only demo into a deliverable reporting workflow. It combines monthly income and expense totals, category spending, budget health, and recent transactions into a downloadable monthly report that can be handed to a stakeholder directly.

Backend API:

- `GET /api/reports/monthly?month=YYYY-MM&format=csv`
- `GET /api/reports/monthly?month=YYYY-MM&format=pdf`

Rules:

- Authentication is required
- Only the current user's data is exported
- `month` must use `YYYY-MM`
- `format` only supports `csv` and `pdf`
- Empty months still export a valid empty report

Report contents include:

- report month
- exported time
- `monthlyIncome`
- `monthlyExpense`
- `monthlyBalance`
- `expenseByCategory`
- `budgetItems`
- `recentTransactions`
- disclaimer

CSV details:

- UTF-8 BOM for Excel compatibility
- Filename: `finance-report-YYYY-MM.csv`
- Sections:
  - `Monthly Summary`
  - `Expense By Category`
  - `Budget Status`
  - `Recent Transactions`

PDF details:

- Generated by backend service
- English-only PDF labels to avoid runtime font issues
- Filename: `finance-report-YYYY-MM.pdf`

## Demo Flow

- Login demo account
- View Dashboard
- Check Budget Health
- Export Monthly Report CSV
- Export Monthly Report PDF
- Review Stock Watchlist

## API Examples

```http
GET /api/reports/monthly?month=2026-05&format=csv
Authorization: Bearer <token>
```

```http
GET /api/reports/monthly?month=2026-05&format=pdf
Authorization: Bearer <token>
```

## Frontend Export Entry

The Dashboard page includes:

- month picker (`input type="month"`)
- `Export CSV` button
- `Export PDF` button
- loading state
- error message

The frontend download flow uses a blob response and preserves the backend filename.

## CI

GitHub Actions workflow runs:

- backend import smoke
- backend `alembic upgrade head`
- backend `compileall`
- backend `pytest`
- frontend `npm ci`
- frontend lint
- frontend build
- frontend tests

Workflow file:

- [ci.yml](.github/workflows/ci.yml)

## Portfolio Value

This project is stronger as a portfolio piece because it demonstrates not only dashboard visualization, but also real deliverable output, backend-generated files, user-scoped reporting, and maintainable cross-layer contracts.
