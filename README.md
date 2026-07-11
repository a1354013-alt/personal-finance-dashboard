# Personal Finance Dashboard

Personal Finance Dashboard is a full-stack portfolio/demo project for tracking expenses, budgets, dashboard analytics, stock watchlists, AI-assisted summaries, monthly report exports, and transaction imports.

The current release is intended for local demo use: it should start from VS Code F5 on Windows, pass backend/frontend tests, build the frontend, and keep API contracts aligned across FastAPI and Vue.

## Project Status

This repository is a portfolio/demo project prepared for the v1.4.0 release.

Implemented demo surface:

- FastAPI backend
- Vue frontend
- Auth with access token, refresh token, and logout revoke flow
- Dashboard analytics
- Transaction editing and recurring transaction planning
- Budget management and budget health summaries
- Stock watchlist
- Taiwan stock technical indicators and in-app price alerts
- Monthly reports
- AI-assisted finance summary
- Transaction import preview/confirm flow
- CSV and PDF export

Demo readiness already in place:

- Backend tests
- Frontend tests
- GitHub Actions CI
- VS Code F5 full-stack startup on Windows

## Features

- Expense and income tracking
- Transaction editing on the Expenses page
- Recurring transactions with weekly, monthly, and yearly schedules
- Monthly budget setup and budget health summaries
- Dashboard cards, monthly forecast, unbudgeted spending insight, charts, recent transactions, and report export
- Stock watchlist with cached market data, Taiwan stock/ETF symbol normalization, MA5/MA20/RSI14 technical indicators, in-app price alerts, sync status, fundamentals screening, AI interpretation notes, and per-item currency display
- AI finance summary and budget advice with deterministic fallback behavior
- Transaction import for CSV/XLSX files with preview, row validation, duplicate detection, and batch history
- CSV and PDF monthly report export
- Demo auth with access tokens, refresh tokens, and logout refresh-token revoke flow

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic, SQLite, pytest
- Frontend: Vue 3, Pinia, Vue Router, vue-i18n, Axios, Vite, Vitest
- Development: VS Code launch/tasks, PowerShell scripts for Windows, optional shell script for macOS/Linux
- Background work: queued sync jobs for market data and fundamentals

## Environment Setup

The app runs with demo-safe defaults. To customize local settings, copy the local environment examples before running the app:

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

Frontend npm commands can be run either from `frontend/` directly or from the repository root through the convenience scripts in the root `package.json`.

## VS Code F5 Startup

Windows is the supported F5 path for this v1.4.0 release.

1. Open the repository root in VS Code.
2. Install the VS Code Python and JavaScript debugging extensions if prompted.
3. Select `F5: Start Personal Finance Dashboard` in Run and Debug.
4. Press F5.

The F5 compound launch runs:

- `scripts/bootstrap-backend.ps1` before the FastAPI debugger starts
- `scripts/bootstrap-frontend.ps1` before the Vite terminal starts
- backend virtual environment bootstrap when `backend\.venv` does not exist yet
- local `.env` copy from `backend\.env.example` or `frontend\.env.example` when missing
- backend requirements installation only when `backend\requirements.txt` changed, then `alembic upgrade head`
- frontend dependency installation only when `frontend\package.json` or `frontend\package-lock.json` changed
- browser launch after the frontend responds
- backend at `http://127.0.0.1:8000`
- frontend at `http://127.0.0.1:5173`
- Swagger UI at `http://127.0.0.1:8000/docs`

The backend runs under the VS Code Python debugger. The frontend runs in a VS Code terminal through Vite, and the browser opens to `http://127.0.0.1:5173`. The frontend dev server proxies `/api` calls to `http://127.0.0.1:8000`.

Demo account after seeding:

- Email: `demo@example.com`
- Password: `demo1234`

If you want to test the bootstrap layer directly without opening VS Code:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap-backend.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap-frontend.ps1
```

## One-Click Windows Script

From the repository root:

```powershell
.\start-dev.bat
```

Or run the PowerShell script directly:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\dev-start.ps1
```

The script checks Python, Node.js, and npm, prepares dependencies, applies migrations, copies missing local env files from examples, opens separate backend/frontend dev-server windows, and opens the frontend URL. `.\scripts\start-dev.ps1` remains as a compatibility wrapper for the same flow.

Manual fallback commands:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

## macOS / Linux Start

```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

The shell script is provided for convenience, but the VS Code F5 workflow is currently documented and verified for Windows.

## Demo Seed Data

```powershell
cd backend
python seed_data.py --reset
```

This creates demo data for:

- demo user
- transactions
- recurring transactions
- budgets
- an unbudgeted current-month spending category
- stock watchlist
- cached stock prices

The default `python seed_data.py --reset` command creates current-month transactions, recurring income/expense schedules, budgets, and one unbudgeted spending category so Dashboard Budget Health, Monthly Forecast, and Unbudgeted Spending are populated immediately after seeding. `--relative-dates` is still available for shifting the older fixed demo records, and it avoids future-dated demo transactions.

Demo account:

- Email: `demo@example.com`
- Password: `demo1234`

Taiwan stock demo flow:

1. Run `python seed_data.py --reset` from `backend`.
2. Start the backend and frontend, then sign in with the demo account.
3. Open Stocks.
4. Add `2330`, `0050`, or `00878`; four-digit Taiwan symbols are normalized to `.TW`.
5. Use Price Sync on the watchlist item.
6. Use AI Interpretation to generate observation notes from cached price data.

Transaction import demo flow:

1. Run the release verification sequence from the repository root.
2. Start the backend and frontend, then sign in with the demo account.
3. Open Import from the top navigation.
4. Upload [docs/demo/sample-transactions.csv](docs/demo/sample-transactions.csv).
5. Review the preview table, validation messages, and duplicate markers.
6. Confirm the valid rows you want to import.
7. Open Dashboard or Expenses to verify the imported records appear.

Smart monthly planning demo flow:

1. Run `python seed_data.py --reset` from `backend`.
2. Start the backend and frontend, then sign in with the demo account.
3. Open Expenses, edit an existing transaction, and save it.
4. Open Recurring from the top navigation and create or adjust a recurring transaction.
5. Open Dashboard and review Monthly Forecast for projected income, projected expense, projected balance, and pending recurring items.
6. Review Unbudgeted Spending to find current-month categories with spending but no active budget.

AI interpretation is informational only and not financial advice. It summarizes cached data, recent price movement, volume/liquidity context, risk notes, and watch points; it does not provide buy/sell recommendations.

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

Repository root convenience:

```powershell
npm run frontend:lint
npm run frontend:test
npm run frontend:build
npm run frontend:audit
```

## v1.3 Stock Indicators and Price Alerts

The v1.3 stock workspace adds technical context and simple in-app alert tracking for Taiwan stock and ETF watchlist items:

- MA5, MA20, and RSI14 are calculated from stored stock price history only.
- Indicator responses include a clear status when price history is insufficient or unavailable.
- Price alerts are user-scoped, in-app only, and support manual above/below target checks against the latest stored watchlist price.
- Alerts are not a real-time background monitoring system yet. Users trigger evaluation with the Stocks page Check Alerts flow.
- There is currently no email notification, push notification, LINE notification, or broker integration.
- Future roadmap may include a background scheduler, email notification, or push notification.
- Stock insights and indicator displays are informational only and not financial advice. The app does not provide buy/sell recommendations or target prices.

Demo flow:

1. Run `python seed_data.py --reset` from `backend/`.
2. Log in with the seeded demo account.
3. Open the Stocks page.
4. View MA5, MA20, and RSI14 for seeded watchlist symbols.
5. Create a price alert for a watchlist item.
6. Run Check Alerts from the Stocks page to manually evaluate alert conditions.
7. Review active or triggered in-app alert state.

## Transaction Import

The v1.2 MVP transaction import flow is intentionally small and safe:

- Supported file types: `.csv` and `.xlsx`
- Maximum upload size: 2 MB
- Flow: upload -> backend preview -> validation and duplicate review -> confirm import
- Duplicate checks cover both repeated rows in the uploaded file and matching rows already in the current user's database
- Import batches are scoped to the authenticated user and can be reviewed again after preview/import

Recognized columns include these common names:

- Date: `date`, `transaction_date`, `日期`, `交易日期`, `入帳日期`, `消費日期`, `付款日期`, `交易日`
- Amount: `amount`, `金額`, `交易金額`
- Type: `type`, `類型`, `收支類型`, `交易類型`, `收支`, `收入支出`
- Category: `category`, `分類`, `類別`
- Description: `description`, `note`, `memo`, `摘要`, `說明`, `備註`
- Payment method: `payment_method`, `payment method`, `支付方式`, `付款方式`

If required columns are missing, the preview endpoint returns a clear validation error instead of guessing a mapping.

## Release Verification

From the repository root, run either of these commands:

```powershell
.\scripts\verify-release.ps1
npm run verify
```

The PowerShell verifier runs the full release validation sequence from the repository root:

- backend `python -m compileall .`
- backend `python -m alembic upgrade head`
- backend `python -m pytest -q`
- backend `python seed_data.py --reset`
- frontend `npm ci`
- frontend `npm run lint`
- frontend `npm run test:run`
- frontend `npm run build`
- frontend `npm audit --audit-level=moderate`

## Build

Frontend production build:

```powershell
cd frontend
npm run build
```

Dependency audit:

```powershell
cd frontend
npm audit --audit-level=moderate
```

## API Naming Notes

The project intentionally keeps naming strategy stable at each layer instead of forcing one naming style everywhere:

- Python services, SQLAlchemy models, and DB-oriented payloads may use `snake_case`
- Vue components, Pinia stores, and display-oriented state use `camelCase`
- Frontend contract normalizers in [frontend/src/api/contracts.js](frontend/src/api/contracts.js) are the boundary that accepts mixed API field styles and returns stable UI shapes

When extending an API response, prefer updating the response model or the matching normalizer rather than renaming every field across the stack in one pass.

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

Report contents include:

- report month
- exported time
- monthly income
- monthly expense
- monthly balance
- expense by category
- budget items
- recent transactions
- disclaimer

CSV details:

- UTF-8 BOM for Excel compatibility
- Filename: `finance-report-YYYY-MM.csv`

PDF details:

- Generated by backend service
- English-only PDF labels to avoid runtime font issues
- Filename: `finance-report-YYYY-MM.pdf`

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

## Rate Limiting

The current rate limiter is an in-memory, demo-level guard intended for a single local API process. It does not share counters across multiple workers or multiple deployed instances. Production deployments should replace it with a Redis-backed or otherwise centralized rate limiter.

## Known Limitations / Roadmap

- Manual column mapping is not implemented yet; the MVP relies on recognized headers and returns a clear missing-column error otherwise.
- Recurring transactions currently support planning and forecasting, but they do not automatically generate real transaction records yet.
- Stock functionality is a watchlist, not a full portfolio profit/loss system.
- Taiwan stock prices are fetched through a replaceable provider interface; local tests use fakes and do not require external market-data access.
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
- backend `python seed_data.py --reset`
- frontend `npm ci`
- frontend lint
- frontend tests
- frontend build
- frontend `npm audit --audit-level=moderate`

Workflow file:

- [.github/workflows/ci.yml](.github/workflows/ci.yml)
