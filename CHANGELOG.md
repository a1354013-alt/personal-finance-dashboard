# Changelog

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
