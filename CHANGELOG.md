# Changelog

## v1.1.0-rc1

- Added the Taiwan stock and ETF watchlist MVP flow for the demo account, including seeded watchlist records and cached stock price examples.
- Added Taiwan symbol normalization so four-digit Taiwan symbols resolve into `.TW` watchlist entries consistently.
- Added explicit price sync status handling so the watchlist and dashboard can surface seeded and synchronized stock data states clearly.
- Added AI stock interpretation output for cached stock data while keeping the Taiwan stock AI disclaimer in place.
- Expanded fake-provider and regression coverage so backend and frontend stock workflows stay testable without external network stock provider calls.
- Refreshed seed demo data to cover Taiwan stock examples, sync-ready price records, and stock dashboard behavior out of the box.
- Release verification status for this candidate: backend 68 passed, frontend 54 passed, and frontend build passed.
