from __future__ import annotations

from datetime import date

from db.database import SessionLocal
from models.budget import BudgetORM
from models.expense import ExpenseORM
from models.recurring_transaction import RecurringTransactionOccurrenceORM, RecurringTransactionORM
from models.stock import StockHoldingORM, StockPriceHistoryORM, WatchlistORM
from models.user import UserORM
from seed_data import DEMO_EMAIL, build_demo_dates, seed
from tests.conftest import auth_headers


def test_seed_reset_creates_current_month_demo_data(client):
    seed(reset=True)
    current_month = date.today().strftime("%Y-%m")

    with SessionLocal() as db:
        demo_user = db.query(UserORM).filter(UserORM.email == DEMO_EMAIL).first()
        assert demo_user is not None
        assert (
            db.query(ExpenseORM)
            .filter(
                ExpenseORM.user_id == demo_user.id,
                ExpenseORM.date >= date.today().replace(day=1),
            )
            .count()
            > 0
        )
        assert (
            db.query(BudgetORM)
            .filter(BudgetORM.user_id == demo_user.id, BudgetORM.month == current_month)
            .count()
            > 0
        )
        taiwan_item = (
            db.query(WatchlistORM)
            .filter(WatchlistORM.user_id == demo_user.id, WatchlistORM.stock_code == "2330.TW")
            .one()
        )
        assert taiwan_item.market == "Taiwan"
        assert taiwan_item.exchange == "TWSE"
        assert taiwan_item.currency == "TWD"
        assert taiwan_item.last_price is not None
        assert taiwan_item.previous_close is not None
        assert taiwan_item.price_change is not None
        assert taiwan_item.change_percent is not None
        assert taiwan_item.volume is not None
        assert taiwan_item.provider == "seed"
        assert taiwan_item.price_updated_at is not None
        assert taiwan_item.sync_status == "ready"
        assert taiwan_item.sync_required == 0
        assert taiwan_item.sync_error is None
        assert taiwan_item.price_sync_status == "success"
        assert db.query(StockPriceHistoryORM).filter(StockPriceHistoryORM.stock_code == "2330.TW").count() > 0
        holdings = db.query(StockHoldingORM).filter(StockHoldingORM.user_id == demo_user.id).all()
        assert len(holdings) >= 3
        assert any(item.stock_code == "2330.TW" for item in holdings)
        active_recurring = (
            db.query(RecurringTransactionORM)
            .filter(RecurringTransactionORM.user_id == demo_user.id, RecurringTransactionORM.is_active.is_(True))
            .all()
        )
        assert active_recurring
        assert all(item.next_run_date is not None for item in active_recurring)
        occurrences = (
            db.query(RecurringTransactionOccurrenceORM)
            .filter(RecurringTransactionOccurrenceORM.user_id == demo_user.id)
            .all()
        )
        assert any(item.status == "generated" for item in occurrences)
        assert any(item.status == "skipped" for item in occurrences)
        generated_occurrence = next(item for item in occurrences if item.status == "generated")
        assert generated_occurrence.scheduled_date == generated_occurrence.recurring_transaction.start_date

    login = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": "demo1234"})
    assert login.status_code == 200
    headers = auth_headers(login.json()["access_token"])
    summary = client.get("/api/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["budgetItems"]
    stocks_dashboard = client.get("/api/stocks/dashboard", headers=headers)
    assert stocks_dashboard.status_code == 200
    stock_payload = stocks_dashboard.json()
    taiwan_by_code = {item["stock_code"]: item for item in stock_payload["watchlist"] if item["stock_code"].endswith(".TW")}
    assert taiwan_by_code["2330.TW"]["currency"] == "TWD"
    assert taiwan_by_code["2330.TW"]["market"] == "Taiwan"
    assert taiwan_by_code["2330.TW"]["last_price"] is not None
    assert stock_payload["price_history"]
    portfolio = client.get("/api/stocks/portfolio", headers=headers)
    assert portfolio.status_code == 200
    portfolio_payload = portfolio.json()
    assert portfolio_payload["holdings_count"] >= 3
    assert portfolio_payload["positions"]
    assert any(position["stock_code"] == "2330.TW" for position in portfolio_payload["positions"])
    indicators = client.get(f"/api/stocks/watchlist/{taiwan_by_code['2330.TW']['id']}/indicators", headers=headers)
    assert indicators.status_code == 200
    indicator_payload = indicators.json()
    assert indicator_payload["status"] == "ready"
    assert indicator_payload["ma5"] is not None
    assert indicator_payload["ma20"] is not None
    assert indicator_payload["rsi14"] is not None


def test_seed_without_reset_replaces_demo_rows_without_duplicate_occurrences():
    seed(reset=True)
    seed()

    with SessionLocal() as db:
        demo_user = db.query(UserORM).filter(UserORM.email == DEMO_EMAIL).one()
        occurrences = (
            db.query(RecurringTransactionOccurrenceORM)
            .filter(RecurringTransactionOccurrenceORM.user_id == demo_user.id)
            .all()
        )

        assert len(occurrences) == 2
        assert len({(item.recurring_transaction_id, item.scheduled_date) for item in occurrences}) == 2


def test_relative_seed_dates_are_not_double_shifted_or_future_dated():
    expenses, prices = build_demo_dates(relative_dates=True)
    today = date.today()

    assert any(item["date"].year == today.year and item["date"].month == today.month for item in expenses)
    assert all(item["date"] <= today for item in expenses)
    assert all(item["trade_date"] <= today for item in prices)
