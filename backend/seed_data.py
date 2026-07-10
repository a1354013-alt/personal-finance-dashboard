from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from calendar import monthrange

from db.database import SessionLocal, init_db, reset_sqlite_db
from models.budget import BudgetORM
from models.expense import ExpenseORM
from models.recurring_transaction import RecurringTransactionORM
from models.stock import StockPriceAlertORM, StockPriceHistoryORM, StockPriceORM, WatchlistORM
from models.user import UserORM
from services.auth import get_password_hash
from services.recurring_transaction_service import derive_next_run_date

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo1234"

FIXED_MOCK_EXPENSES = [
    {"amount": 50000.0, "category": "Salary", "type": "income", "date": date(2026, 2, 5), "note": "Monthly salary"},
    {"amount": 9200.0, "category": "Food", "type": "expense", "date": date(2026, 2, 10), "note": "Dining and groceries"},
    {"amount": 3600.0, "category": "Transport", "type": "expense", "date": date(2026, 2, 12), "note": "Metro and taxi"},
    {"amount": 12500.0, "category": "Housing", "type": "expense", "date": date(2026, 2, 1), "note": "Rent"},
    {"amount": 1800.0, "category": "Utilities", "type": "expense", "date": date(2026, 2, 15), "note": "Utilities"},
    {"amount": 50000.0, "category": "Salary", "type": "income", "date": date(2026, 3, 5), "note": "Monthly salary"},
    {"amount": 5000.0, "category": "Freelance", "type": "income", "date": date(2026, 3, 18), "note": "Side project"},
    {"amount": 8400.0, "category": "Food", "type": "expense", "date": date(2026, 3, 8), "note": "Dining and groceries"},
    {"amount": 3400.0, "category": "Transport", "type": "expense", "date": date(2026, 3, 14), "note": "Metro and taxi"},
    {"amount": 12500.0, "category": "Housing", "type": "expense", "date": date(2026, 3, 1), "note": "Rent"},
    {"amount": 4600.0, "category": "Entertainment", "type": "expense", "date": date(2026, 3, 20), "note": "Weekend trip"},
    {"amount": 50000.0, "category": "Salary", "type": "income", "date": date(2026, 4, 5), "note": "Monthly salary"},
    {"amount": 9800.0, "category": "Food", "type": "expense", "date": date(2026, 4, 6), "note": "Dining and groceries"},
    {"amount": 3200.0, "category": "Transport", "type": "expense", "date": date(2026, 4, 7), "note": "Metro and taxi"},
    {"amount": 12500.0, "category": "Housing", "type": "expense", "date": date(2026, 4, 1), "note": "Rent"},
    {"amount": 2900.0, "category": "Utilities", "type": "expense", "date": date(2026, 4, 8), "note": "Utilities"},
    {"amount": 6200.0, "category": "Healthcare", "type": "expense", "date": date(2026, 4, 9), "note": "Clinic and medicine"},
    {"amount": 2800.0, "category": "Travel", "type": "expense", "date": date(2026, 5, 2), "note": "Future booking"},
    {"amount": 50000.0, "category": "Salary", "type": "income", "date": date.today(), "note": "Current month salary"},
    {"amount": 1500.0, "category": "Food", "type": "expense", "date": date.today(), "note": "Lunch"},
    {"amount": 2200.0, "category": "Shopping", "type": "expense", "date": date.today(), "note": "Unbudgeted household item"},
]

MOCK_BUDGETS = [
    {"category": "Food", "amount": 9000.0},
    {"category": "Transport", "amount": 3500.0},
    {"category": "Housing", "amount": 13000.0},
    {"category": "Utilities", "amount": 2500.0},
    {"category": "Healthcare", "amount": 5000.0},
]

MOCK_WATCHLIST = [
    {"stock_code": "2330.TW", "name": "TSMC"},
    {"stock_code": "2317.TW", "name": "Hon Hai"},
    {"stock_code": "AAPL", "name": "Apple"},
]

FIXED_MOCK_PRICES = [
    {
        "stock_code": "2330.TW",
        "trade_date": date(2026, 4, 9),
        "close": 850.0,
        "previous_close": 842.0,
        "open": 845.0,
        "high": 855.0,
        "low": 840.0,
        "volume": 25000,
    },
    {
        "stock_code": "2317.TW",
        "trade_date": date(2026, 4, 9),
        "close": 168.5,
        "previous_close": 166.0,
        "open": 165.0,
        "high": 170.0,
        "low": 164.0,
        "volume": 45000,
    },
    {
        "stock_code": "AAPL",
        "trade_date": date(2026, 4, 9),
        "close": 172.3,
        "previous_close": 171.8,
        "open": 170.0,
        "high": 175.0,
        "low": 169.0,
        "volume": 55000000,
    },
]

MOCK_RECURRING_TRANSACTIONS = [
    {"amount": 50000.0, "category": "Salary", "type": "income", "note": "Monthly salary", "frequency": "monthly", "day": 5},
    {"amount": 12500.0, "category": "Housing", "type": "expense", "note": "Monthly rent", "frequency": "monthly", "day": 1},
    {"amount": 1800.0, "category": "Utilities", "type": "expense", "note": "Utility bill", "frequency": "monthly", "day": 20},
]


def _build_history_series(latest_price: dict) -> list[dict]:
    latest_trade_date = latest_price["trade_date"]
    latest_close = float(latest_price["close"])
    rows: list[dict] = []
    for offset in range(24, -1, -1):
        trade_date = date.fromordinal(latest_trade_date.toordinal() - offset)
        close = latest_close - (offset * 2.0)
        rows.append(
            {
                "stock_code": latest_price["stock_code"],
                "trade_date": trade_date,
                "close": close,
                "open": close - 1.0,
                "high": close + 3.0,
                "low": close - 3.0,
                "volume": int(latest_price["volume"] or 0) + ((24 - offset) * 100),
            }
        )
    rows[-1] = {key: value for key, value in latest_price.items() if key != "previous_close"}
    return rows


def _stock_market_fields(stock_code: str) -> dict:
    if stock_code.endswith(".TW"):
        return {"market": "Taiwan", "exchange": "TWSE", "currency": "TWD"}
    if stock_code.endswith(".TWO"):
        return {"market": "Taiwan", "exchange": "TPEx", "currency": "TWD"}
    return {"market": "US", "exchange": None, "currency": "USD"}


def _price_change_fields(price: dict) -> dict:
    previous_close = price.get("previous_close")
    close = price["close"]
    price_change = None
    change_percent = None
    if previous_close not in (None, 0):
        price_change = close - previous_close
        change_percent = (price_change / previous_close) * 100
    return {
        "last_price": close,
        "previous_close": previous_close,
        "price_change": price_change,
        "change_percent": change_percent,
    }


def _shift_date_by_months(value: date, months_delta: int) -> date:
    target_month_index = (value.year * 12 + (value.month - 1)) + months_delta
    target_year = target_month_index // 12
    target_month = (target_month_index % 12) + 1
    max_day = monthrange(target_year, target_month)[1]
    return date(target_year, target_month, min(value.day, max_day))


def _not_future(value: date) -> date:
    today = date.today()
    return today if value > today else value


def build_demo_dates(relative_dates: bool) -> tuple[list[dict], list[dict]]:
    if not relative_dates:
        return FIXED_MOCK_EXPENSES, FIXED_MOCK_PRICES

    fixed_anchor = date(2026, 4, 1)
    current_anchor = date.today().replace(day=1)
    anchor_delta = (current_anchor.year - fixed_anchor.year) * 12 + (current_anchor.month - fixed_anchor.month)

    relative_expenses: list[dict] = []
    for item in FIXED_MOCK_EXPENSES:
        shifted_item = dict(item)
        if item["date"].year == date.today().year and item["date"].month == date.today().month:
            shifted_item["date"] = item["date"]
        else:
            shifted_item["date"] = _not_future(_shift_date_by_months(item["date"], anchor_delta))
        relative_expenses.append(shifted_item)

    relative_prices: list[dict] = []
    for item in FIXED_MOCK_PRICES:
        original_trade_date = item["trade_date"]
        shifted_trade_date = _shift_date_by_months(original_trade_date, anchor_delta)
        shifted_item = dict(item)
        shifted_item["trade_date"] = _not_future(shifted_trade_date)
        relative_prices.append(shifted_item)

    return relative_expenses, relative_prices


def seed(reset: bool = False, relative_dates: bool = False) -> None:
    if reset:
        reset_sqlite_db()
    else:
        init_db()

    mock_expenses, mock_prices = build_demo_dates(relative_dates)
    budget_month = date.today().strftime("%Y-%m")

    db = SessionLocal()
    try:
        demo_user = db.query(UserORM).filter(UserORM.email == DEMO_EMAIL).first()
        if not demo_user:
            demo_user = UserORM(email=DEMO_EMAIL, password_hash=get_password_hash(DEMO_PASSWORD))
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

        db.query(ExpenseORM).filter(ExpenseORM.user_id == demo_user.id).delete()
        db.query(RecurringTransactionORM).filter(RecurringTransactionORM.user_id == demo_user.id).delete()
        db.query(BudgetORM).filter(BudgetORM.user_id == demo_user.id).delete()
        db.query(StockPriceAlertORM).filter(StockPriceAlertORM.user_id == demo_user.id).delete()
        db.query(WatchlistORM).filter(WatchlistORM.user_id == demo_user.id).delete()
        db.query(StockPriceORM).filter(StockPriceORM.stock_code.in_([item["stock_code"] for item in mock_prices])).delete(
            synchronize_session=False
        )
        db.query(StockPriceHistoryORM).filter(
            StockPriceHistoryORM.stock_code.in_([item["stock_code"] for item in mock_prices])
        ).delete(synchronize_session=False)
        db.commit()

        for item in mock_expenses:
            db.add(ExpenseORM(user_id=demo_user.id, **item))

        for item in MOCK_BUDGETS:
            db.add(BudgetORM(user_id=demo_user.id, month=budget_month, **item))

        today = date.today()
        for item in MOCK_RECURRING_TRANSACTIONS:
            run_day = min(item["day"], monthrange(today.year, today.month)[1])
            start_date = date(today.year, today.month, run_day)
            db.add(
                RecurringTransactionORM(
                    user_id=demo_user.id,
                    amount=item["amount"],
                    category=item["category"],
                    type=item["type"],
                    note=item["note"],
                    frequency=item["frequency"],
                    start_date=start_date,
                    end_date=None,
                    next_run_date=derive_next_run_date(start_date, item["frequency"], None, today=today),
                    is_active=True,
                )
            )

        price_by_code = {item["stock_code"]: item for item in mock_prices}
        seeded_at = datetime.now(timezone.utc)
        for item in MOCK_WATCHLIST:
            stock_code = item["stock_code"]
            price = price_by_code.get(stock_code)
            market_fields = _stock_market_fields(stock_code)
            price_fields = _price_change_fields(price) if price else {}
            db.add(
                WatchlistORM(
                    user_id=demo_user.id,
                    market=market_fields["market"],
                    exchange=market_fields["exchange"],
                    currency=market_fields["currency"],
                    volume=price["volume"] if price else None,
                    provider="seed",
                    price_updated_at=seeded_at if price else None,
                    sync_status="ready" if price else "sync_required",
                    sync_required=0 if price else 1,
                    sync_error=None,
                    price_sync_status="success",
                    last_sync_error=None,
                    last_sync_attempt_at=seeded_at,
                    **price_fields,
                    **item,
                )
            )

        for item in mock_prices:
            for history_row in _build_history_series(item):
                db.add(StockPriceHistoryORM(source="seed", **history_row))
            price_row = {key: value for key, value in item.items() if key != "previous_close"}
            db.add(StockPriceORM(**price_row))

        db.commit()

        print("Seed completed successfully.")
        print(f"Demo email: {DEMO_EMAIL}")
        print(f"Demo password: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data for Personal Finance Dashboard.")
    parser.add_argument("--reset", action="store_true", help="Delete the SQLite database first and recreate it.")
    parser.add_argument(
        "--relative-dates",
        action="store_true",
        help="Shift the fixed demo dataset to recent months while keeping deterministic record shapes.",
    )
    args = parser.parse_args()
    seed(reset=args.reset, relative_dates=args.relative_dates)
