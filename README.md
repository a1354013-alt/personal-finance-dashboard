# Personal Finance Dashboard

> Full-stack personal finance dashboard with budgeting, expense tracking, stock watchlist, and AI insights — built with FastAPI + Vue 3.

## Feature Table

| Feature | Description |
|--------|-------------|
| Budget Management | Monthly category budgets with status tracking (Safe/Warning/Overspent) and historical month selection |
| Expense Logging | Track income/expense records with categories, dates, and optional notes |
| Dashboard | Aggregated insights (totals, trends, category breakdown, recent transactions, AI summaries) |
| Stocks Watchlist | Track selected symbols and sync cached prices/fundamentals |
| AI Insights | Generate deterministic summaries/advice with provider metadata |

## Screenshots

![Dashboard](assets/screenshots/dashboard.svg)
![Expenses](assets/screenshots/expenses.svg)
![Budgets](assets/screenshots/budgets.svg)
![Stocks Watchlist](assets/screenshots/stocks-watchlist.svg)

## Architecture Overview

- Backend: FastAPI routers + Pydantic response contracts + SQLAlchemy ORM + Alembic migrations
- Frontend: Vue 3 pages + Pinia stores + Axios API client + contract normalizers
- Database: SQLite by default (via `DATABASE_URL`)
- External Providers: LLM provider (OpenAI/fallback/mock), fundamentals provider (`yfinance`) with DB cache

High-level flow:

```text
Frontend (Vue)
       ↓
API (FastAPI Routers)
       ↓
Services
       ↓
Database + Providers
```

## Data Flow

```text
User → Router → Service → DB → Response → Frontend Store → UI
```

## Quick Start

### 1) Environment

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

### 2) Backend (FastAPI)

```bash
cd backend
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

Optional (SQLite demo data/reset):

```bash
cd backend
python seed_data.py --reset
```

Backend URLs:

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### 3) Frontend (Vue 3)

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: http://localhost:5173

## API Design Principles

- RESTful routes with clear resource boundaries (`/api/expenses`, `/api/budgets`, `/api/stocks/*`, `/api/ai/*`)
- `204 No Content` for successful DELETE (empty body)
- Normalized responses (typed response models; consistent serialization for money/date fields)
- User-scoped resources (JWT bearer auth; CRUD is scoped to the current user)

## Testing Strategy

- Backend: `pytest` (SQLite in-memory), provider calls mocked in tests
- Frontend: `vitest` + `@vue/test-utils` + `jsdom`
- Contract tests: validate serialization + response shape (no user-scoped leakage)
- Smoke tests: end-to-end API flows (auth → CRUD → dashboard aggregates)

## Why This Project Stands Out

- Provider abstraction design
- Shared cache architecture
- API contract normalization
- Full CI pipeline
- Production-style layering

## CI

GitHub Actions workflow runs on clean machines:

- backend: import smoke + `alembic upgrade head` smoke + `compileall` + `pytest`
- frontend: `lint` + `test` + `build`

See `.github/workflows/ci.yml`.

## Budget Management Features

The new Monthly Budget Management provides:
- **Month Selection**: Manage budgets for any specific month.
- **Budget Summary**: Real-time calculation of total budget, used amount, and remaining balance.
- **Status Tracking**: Visual indicators for budget health (Safe < 80%, Warning 80-100%, Overspent > 100%).
- **CRUD Operations**: Create, update, and delete budgets per category per month.

### API Endpoints (Budgets)

- `GET /api/budgets?month=YYYY-MM`: List budgets for a specific month.
- `GET /api/budgets/summary?month=YYYY-MM`: Get detailed budget usage summary.
- `POST /api/budgets`: Create or update a budget.
- `PUT /api/budgets/{id}`: Update budget amount.
- `DELETE /api/budgets/{id}`: Remove a budget.

## Dashboard Features

The Visual Dashboard integrates budget status:
- **Summary Cards**: Monthly income, expense, balance, and **remaining budget**.
- **Budget Health Widget**: Quick view of all category budget statuses with progress bars.
- **Monthly Trend**: 6-month historical view of income vs. expenses.
- **Category Breakdown**: Donut chart showing expense distribution.
- **Recent Transactions**: Quick view of the last 10 activities.
- **AI Insights**: Automated financial summary and budget advice.

### API Endpoints (Dashboard)

- `GET /api/dashboard/summary`: Returns current month totals, trend, category breakdown, recent transactions, and **integrated budget summary**.
- `GET /api/dashboard/charts`: Returns detailed chart data.

### Tech Stack (Dashboard)

- **Frontend**: Vue 3, Pinia, Chart.js
- **Backend**: FastAPI, SQLAlchemy, Pydantic

## Future Improvements

- Recurring transactions
- Budget alerts
- Export reports
- Multi-currency support

