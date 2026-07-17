# Changelog

## v1.6.0

- Fixed dangling symbolic-link handling in seeded Playwright E2E database validation so SQLite cannot create an external target through `backend/.e2e/playwright-e2e*.db`.
- Hardened seeded Playwright E2E database isolation so resets are limited to `backend/.e2e/playwright-e2e*.db` and normal databases such as `finance.db`, `test_smoke.db`, `production.db`, and `audit.db` are rejected.
- Added clean-machine Playwright Chromium installation to local release verification through `npm run e2e:install-browser`, while keeping CI on `npx playwright install --with-deps chromium`.
- Strengthened E2E cleanup on Windows with process-tree termination and post-run checks for lingering `8001`/`5174` ports.
- Promoted `v1.6.0-rc3` to the final `v1.6.0` release.
- Hardened stock portfolio totals so mixed-currency holdings are grouped by currency instead of being combined into one misleading top-level number without FX conversion.
- Added explicit portfolio warnings and grouped currency totals to the Stocks API and Stocks page when a portfolio contains multiple currencies.
- Extended grouped portfolio totals with partial-price metadata: `priced_holdings_count`, `missing_price_count`, `unpriced_cost`, and `is_partial`.
- Hardened holding updates so changing `stock_code` re-infers the holding currency from the normalized symbol when the client does not explicitly provide a currency.
- Fixed duplicate-holding update errors so attempts such as `MSFT -> AAPL` report the intended target symbol and preserve the original holding.
- Added backend and frontend regression coverage for mixed-currency portfolio summaries, grouped totals rendering, allocation safety, stock-code currency re-inference, and partial-price portfolio states.
- Added migration regression coverage for duplicate holding consolidation from revision `0009_add_stock_holdings` to `0010_enforce_unique_stock_holdings`.
- Updated release documentation for the dedicated E2E database namespace, allowed filename pattern, browser cache behavior, and direct local E2E commands.
- Updated application version metadata to `1.6.0`.

## v1.6.0-rc1

- Added stock portfolio holdings with user-scoped CRUD APIs at `GET/POST/PUT/DELETE /api/stocks/holdings`.
- Added `GET /api/stocks/portfolio` for deterministic unrealized P/L, allocation, warning, and position summary data based on cached latest prices.
- Added a Portfolio Holdings section on the Stocks page for creating, editing, deleting, and reviewing holdings alongside market value, cost basis, unrealized P/L, and allocation.
- Refreshed demo seed data with Taiwan and US holdings so the demo account shows positive and negative unrealized P/L immediately after reset.
- Added backend and frontend regression coverage for holdings CRUD, portfolio summary contracts, missing-price handling, and the new Stocks page portfolio flows.
- Kept Playwright E2E smoke deferred for this release candidate to avoid destabilizing the current release gate.
- Updated application version metadata to `1.6.0-rc1`.

## v1.5.0

- Promoted `v1.5.0-rc1` to the final `v1.5.0` release.
- Added recurring transaction occurrence automation with Alembic migration `0008_add_recurring_transaction_occurrences`, current-month recurring transaction generation, per-occurrence generate and skip actions, and user-scoped occurrence APIs.
- Added manual transaction import column mapping for CSV/XLSX preview when automatic required-header detection is incomplete, while keeping duplicate detection and preview-first import behavior intact.
- Hardened dashboard monthly forecast handling so overdue current-month pending recurring occurrences are included while generated or skipped occurrences do not inflate the projection.
- Hardened recurring occurrence month query validation so invalid `YYYY-MM` values are rejected consistently.
- Hardened manual import mapping validation so unsupported fields and duplicate resolved source columns are rejected before preview/import continues.
- Refreshed seed/demo data with more consistent recurring occurrence dates, generated/skipped occurrence examples, and an unmapped CSV fixture for the import mapping flow.
- Validation status for the final release: backend compileall, Alembic upgrade, pytest, seed reset, frontend lint, tests, build, audit, and VS Code F5 JSON checks passed; Playwright E2E smoke coverage remains deferred for a follow-up pass.
- Updated application version metadata to `1.5.0`.

## v1.4.0

- Added user-scoped transaction editing through `PUT /api/expenses/{id}` and the Expenses page edit flow.
- Added recurring transactions with CRUD, deactivate support, Alembic migration `0007_add_recurring_transactions`, and a dedicated frontend page.
- Added dashboard monthly forecast fields based on current-month actuals, pending recurring transactions, and budget context.
- Added unbudgeted spending insight for current-month expense categories without active budgets.
- Hardened recurring transaction `next_run_date` derivation for active schedules.
- Preserved inactive recurring transaction status when editing existing items.
- Cleaned up README limitation wording for current demo behavior.
- Hardened dashboard planning tests against end-of-month timing flakiness.
- Updated demo seed data with recurring income, recurring expenses, current-month forecast data, and an unbudgeted spending category.
- Updated application version metadata to `1.4.0`.

## v1.3.0

- Added stored-history MA5, MA20, and RSI14 stock indicators.
- Added in-app stock price alerts with user-scoped alert APIs.
- Added frontend indicator and alert UI on the existing Stocks page.
- Fixed README transaction import recognized column aliases.
- Fixed transaction import database duplicate detection for re-uploaded expenses when CSV/XLSX rows include `payment_method`.
- Reduced Vite chunk-size pressure with route-level lazy loading.
- Updated application version metadata to `1.3.0`.

## v1.2.0-rc1

- Added CSV and XLSX transaction import with a preview-first workflow before any transactions are created.
- Added row-level validation, duplicate detection against uploaded rows and existing user data, and user-scoped import batch history/detail endpoints.
- Added a frontend Transaction Import page with preview summaries, row status badges, selectable valid rows, and final import results.
- Added backend and frontend import tests plus a sample CSV demo file for local walkthroughs.
- Updated application version metadata to `1.2.0-rc1`.

## v1.1.0-rc1

- Added the Taiwan stock and ETF watchlist MVP flow for the demo account, including seeded watchlist records and cached stock price examples.
- Added Taiwan symbol normalization so four-digit Taiwan symbols resolve into `.TW` watchlist entries consistently.
- Added explicit price sync status handling so the watchlist and dashboard can surface seeded and synchronized stock data states clearly.
- Added AI stock interpretation output for cached stock data while keeping the Taiwan stock AI disclaimer in place.
- Expanded fake-provider and regression coverage so backend and frontend stock workflows stay testable without external network stock provider calls.
- Refreshed seed demo data to cover Taiwan stock examples, sync-ready price records, and stock dashboard behavior out of the box.
- Release verification status for this candidate: backend 68 passed, frontend 54 passed, and frontend build passed.
