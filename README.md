# Personal Finance Dashboard

Personal Finance Dashboard is a full-stack portfolio/demo project for tracking expenses, budgets, dashboard analytics, stock watchlists, portfolio holdings, AI-assisted summaries, monthly report exports, and transaction imports.

The current release is intended for local demo use: it should start from VS Code F5 on Windows, pass backend/frontend tests, build the frontend, and keep API contracts aligned across FastAPI and Vue.

## Project Status

This repository is a portfolio/demo project prepared for the v1.7.0-rc1 release.

Implemented demo surface:

- FastAPI backend
- Vue frontend
- Auth with access token, refresh token, and logout revoke flow
- Dashboard analytics
- Transaction editing and recurring transaction planning/automation
- Budget management and budget health summaries
- Stock watchlist
- Portfolio holdings with currency-safe unrealized P/L
- Taiwan stock technical indicators and in-app price alerts
- Monthly reports
- AI-assisted finance summary
- Transaction import preview/confirm flow with manual column mapping fallback
- CSV and PDF export

Demo readiness already in place:

- Backend tests
- Frontend tests
- GitHub Actions CI
- VS Code F5 full-stack startup on Windows

## Features

- Expense and income tracking
- Transaction editing on the Expenses page
- Recurring transactions with weekly, monthly, and yearly schedules plus current-month occurrence generation
- Monthly budget setup and budget health summaries
- Dashboard cards, monthly forecast, unbudgeted spending insight, charts, recent transactions, and report export
- Stock watchlist with cached market data, Taiwan stock/ETF symbol normalization, portfolio holdings, unrealized P/L summary, MA5/MA20/RSI14 technical indicators, in-app price alerts, sync status, fundamentals screening, AI interpretation notes, and per-item currency display
- AI finance summary and budget advice with deterministic fallback behavior
- Transaction import for CSV/XLSX files with preview, optional manual column mapping, row validation, duplicate detection, and batch history
- CSV and PDF monthly report export
- Demo auth with access tokens, refresh tokens, and logout refresh-token revoke flow

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic, SQLite, pytest
- Frontend: Vue 3, Pinia, Vue Router, vue-i18n, Axios, Vite, Vitest
- Development: VS Code launch/tasks, PowerShell scripts for Windows, optional shell script for macOS/Linux
- Background work: queued sync jobs for market data and fundamentals

## Environment Setup

The app runs with demo-safe defaults. `backend/.env.example` is the authoritative backend environment template. To customize local settings, copy the local environment examples before running the app:

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

Supported local runtimes:

- Backend: Python 3.11 or 3.12
- Frontend: Node 20.19.x or Node 22.12.x+

Bootstrap and release scripts fail early when these versions are not met. Backend bootstrap stamps the Python major/minor version with the dependency hash so a virtual environment created with a different interpreter is reinstalled or rejected.

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

Windows is the supported F5 path for this v1.7.0-rc1 release.

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
- backend dependency stamps include the actual virtual-environment Python major/minor version
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
- recurring occurrence automation examples
- budgets
- an unbudgeted current-month spending category
- stock watchlist
- stock portfolio holdings
- cached stock prices

The default `python seed_data.py --reset` command creates current-month transactions, recurring income/expense schedules, generated/skipped recurring occurrence examples, budgets, and one unbudgeted spending category so Dashboard Budget Health, Monthly Forecast, and Unbudgeted Spending are populated immediately after seeding. `--relative-dates` is still available for shifting the older fixed demo records, and it avoids future-dated demo transactions.

Demo account:

- Email: `demo@example.com`
- Password: `demo1234`

Portfolio and stock demo flow:

1. Run `python seed_data.py --reset` from `backend`.
2. Start the backend and frontend, then sign in with the demo account.
3. Open Stocks.
4. Review the seeded portfolio summary and unrealized P/L cards.
5. Add or edit a holding such as `2330` or `AAPL`; four-digit Taiwan symbols are normalized to `.TW`.
6. Check each position's cost basis, market value, allocation, and unrealized P/L.
7. Use Price Sync on a watchlist item if you want to refresh cached price data.
8. Use AI Interpretation to generate observation notes from cached price data.

Transaction import demo flow:

1. Run the release verification sequence from the repository root.
2. Start the backend and frontend, then sign in with the demo account.
3. Open Import from the top navigation.
4. Upload [docs/demo/sample-transactions.csv](docs/demo/sample-transactions.csv) for the normal flow, or [frontend/public/demo/sample-transactions-unmapped.csv](frontend/public/demo/sample-transactions-unmapped.csv) to exercise manual mapping.
5. If required headers are missing, map uploaded columns to `date`, `amount`, and any optional fields you want to carry through.
6. Review the preview table, validation messages, and duplicate markers.
7. Confirm the valid rows you want to import.
8. Open Dashboard or Expenses to verify the imported records appear.

Smart monthly planning demo flow:

1. Run `python seed_data.py --reset` from `backend`.
2. Start the backend and frontend, then sign in with the demo account.
3. Open Expenses, edit an existing transaction, and save it.
4. Open Recurring from the top navigation and create or adjust a recurring transaction.
5. Use Generate This Month or Mark as Paid on a pending occurrence.
6. Open Dashboard and review Monthly Forecast for projected income, projected expense, projected balance, and pending recurring items.
7. Review Unbudgeted Spending to find current-month categories with spending but no active budget.

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

If required columns are missing, the preview endpoint now returns a mapping-required preview state so the user can map uploaded columns before re-running preview.

## Release Verification

From the repository root, run either of these commands:

```powershell
.\scripts\verify-release.ps1
npm run verify
```

The PowerShell verifier runs the full release validation sequence from the repository root:

- backend `python -m compileall .`
- backend `python -m alembic upgrade head`
- backend `python -m alembic check`
- backend `python -m pytest -q`
- backend `python -m pip check`
- backend `python seed_data.py --reset`
- frontend `npm run check:node`
- frontend `npm ci`
- frontend `npm run e2e:install-browser`
- frontend `npm run lint`
- frontend `npm run test:run`
- frontend `npm run build`
- frontend `npm audit --audit-level=moderate`
- frontend `npm run test:e2e-config`
- frontend `npm run e2e:seeded`

Playwright seeded-demo smoke can also be run directly:

```powershell
cd frontend
npm ci
npm run e2e:install-browser
npm run e2e:seeded
```

The smoke test starts isolated backend and frontend servers on `127.0.0.1:8001` and `127.0.0.1:5174`, resets only the validated SQLite database at `backend/.e2e/playwright-e2e.db`, signs in as `demo@example.com`, verifies authentication and protected-route redirection, checks separate TWD and USD portfolio summaries plus separate TWD and USD realized-P/L summaries, confirms seeded Trade History visibility, confirms Opening Balance rows stay read-only, creates a deterministic BUY, creates a valid SELL, verifies holding-projection changes, rejects oversells, deletes the SELL, deletes the BUY, confirms the original holding projection is restored, runs the existing legacy holding create/edit/delete smoke, and confirms logout redirects protected routes back to login. Normal `DATABASE_URL` is ignored by the E2E launcher; only `E2E_DATABASE_URL` can override the path. Overrides must resolve inside `backend/.e2e/`, use a filename matching `playwright-e2e*.db`, and cannot point at normal databases such as `finance.db`, `test_smoke.db`, `production.db`, `audit.db`, or arbitrary names like `custom.db`. The full release verifier installs Playwright Chromium with `npm run e2e:install-browser` after `npm ci`; this uses Playwright's cache when the matching browser is already present. The test database, journal, WAL, and SHM files are deleted on cleanup.

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

## Portfolio Currency Behavior

`GET /api/stocks/portfolio` keeps position-level values in each holding's stored currency and returns a `currency_totals` collection for summary math. Each currency total includes `currency`, `total_cost`, `total_market_value`, `total_unrealized_pnl`, `total_unrealized_pnl_percent`, `priced_cost`, `unpriced_cost`, `holdings_count`, `priced_holdings_count`, `missing_price_count`, and `is_partial`.

Mixed TWD/USD portfolios are not converted or added together in this release. The legacy top-level total fields are populated only for single-currency portfolios; mixed-currency responses use `currency: null` and separate `currency_totals`. When a currency has both priced and unpriced holdings, `total_cost` remains the full cost basis, while `total_market_value`, P/L, and P/L percent are priced-only values marked by `is_partial: true`.

Stock positions are now backed by an auditable trade ledger in `stock_trades`, with FIFO replay used to rebuild the `stock_holdings` projection after every trade mutation. Migration `0011_add_stock_trade_ledger` backfills one `OPENING_BALANCE` trade per legacy holding, preserves user scoping and normalized symbols, and keeps `stock_holdings` as a derived materialized projection instead of the canonical source of truth.

Trade ledger rules for `v1.7.0-rc1`:

- Supported trade types are `OPENING_BALANCE`, `BUY`, and `SELL`.
- FIFO replay order is deterministic: `trade_date`, then `created_at`, then `id`.
- Realized profit/loss is based on trade prices, FIFO matched cost basis, fees, and taxes only.
- Unrealized profit/loss remains in the portfolio section and is never mixed into realized P/L.
- TWD and USD totals remain grouped by currency with no FX-converted grand total.
- Direct holding create/edit/delete remains as a legacy compatibility path that manages only the opening-balance trade. Once `BUY` or `SELL` history exists for a symbol, direct holding edits return a conflict and the position must be managed through the trade ledger.
- `stock_holdings` continues to drive portfolio positions, but it is always rebuilt from the trade ledger in the same transaction as each trade mutation.
- The demo seed now includes profitable and losing realized sales, fees, taxes, partial sells, and remaining open positions in both TWD and USD.

Validation commands for `v1.7.0-rc1`:

```powershell
cd backend
python -m compileall .
python -m alembic upgrade head
python -m pytest -q
python seed_data.py --reset

cd ..\frontend
npm run lint
npm run test:run
npm run build
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

- Multiple FIFO acquisition lots are reconstructed from `OPENING_BALANCE` and `BUY` trade history, while `stock_holdings` remains an aggregated materialized projection per user and stock code. Persisted lot-match inspection is not exposed yet, user-selectable tax-lot matching is not implemented, and LIFO or average-cost accounting are not supported.
- Portfolio unrealized P/L depends on whichever latest cached price is available for each holding; when price data is missing, price-dependent fields are intentionally returned as `null` with warnings.
- Portfolio totals are grouped by holding currency. FX conversion is not implemented yet, so mixed-currency portfolios are shown as separate currency totals and are not combined into one top-level number.
- Taiwan stock prices are fetched through a replaceable provider interface; local tests use fakes and do not require external market-data access.
- `zh-CN` and `ja` keep key parity for the new portfolio strings, but the wording is still largely English and should be localized in a follow-up polish pass.
- PDF report labels are currently mostly English to avoid Chinese font environment issues.

## Common Issues

- Missing Python packages: run `backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`.
- Missing frontend packages: run `npm ci` in `frontend`.
- Unsupported runtime: use Python 3.11/3.12 and Node 20.19.x or 22.12.x+.
- Alembic or SQLite state looks stale: from `backend`, run `.\.venv\Scripts\python.exe -m alembic upgrade head`.
- Port already in use: stop the existing process on ports `8000` or `5173`, or change the launch/script port arguments.
- OpenAI key missing: AI endpoints degrade to deterministic fallback text unless a real provider and key are configured.
- `npm audit` reports issues after dependency updates: inspect the vulnerable package path first and prefer compatible patch/minor upgrades before major upgrades.

## CI

GitHub Actions runs:

- backend import smoke
- backend Alembic migration smoke
- backend Alembic drift check
- backend `python -m compileall .`
- backend `python -m pytest -q`
- backend `python -m pip check`
- backend `python seed_data.py --reset`
- frontend `npm ci`
- frontend lint
- frontend tests
- frontend build
- frontend `npm audit --audit-level=moderate`
- dedicated Playwright seeded-demo smoke with failure artifacts

Workflow file:

- [.github/workflows/ci.yml](.github/workflows/ci.yml)
