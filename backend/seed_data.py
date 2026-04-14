from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from calendar import monthrange

from db.database import SessionLocal, init_db, reset_sqlite_db
from models.budget import BudgetORM
from models.expense import ExpenseORM
from models.stock import StockPriceORM, WatchlistORM
from models.user import UserORM
from services.auth import get_password_hash

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
]

MOCK_BUDGETS = [
    {"category": "Food", "monthly_limit": 9000.0},
    {"category": "Transport", "monthly_limit": 3500.0},
    {"category": "Housing", "monthly_limit": 13000.0},
    {"category": "Utilities", "monthly_limit": 2500.0},
    {"category": "Healthcare", "monthly_limit": 5000.0},
]

MOCK_WATCHLIST = [
    {"stock_code": "2330.TW", "name": "TSMC"},
    {"stock_code": "2317.TW", "name": "Hon Hai"},
    {"stock_code": "AAPL", "name": "Apple"},
]

FIXED_MOCK_PRICES = [
    {"stock_code": "2330.TW", "trade_date": "2026-04-09", "close": 850.0, "open": 845.0, "high": 855.0, "low": 840.0, "volume": 25000.0},
    {"stock_code": "2317.TW", "trade_date": "2026-04-09", "close": 168.5, "open": 165.0, "high": 170.0, "low": 164.0, "volume": 45000.0},
    {"stock_code": "AAPL", "trade_date": "2026-04-09", "close": 172.3, "open": 170.0, "high": 175.0, "low": 169.0, "volume": 55000000.0},
]


def _shift_date_by_months(value: date, months_delta: int) -> date:
    target_month_index = (value.year * 12 + (value.month - 1)) + months_delta
    target_year = target_month_index // 12
    target_month = (target_month_index % 12) + 1
    max_day = monthrange(target_year, target_month)[1]
    return date(target_year, target_month, min(value.day, max_day))


def build_demo_dates(relative_dates: bool) -> tuple[list[dict], list[dict]]:
    if not relative_dates:
        return FIXED_MOCK_EXPENSES, FIXED_MOCK_PRICES

    fixed_anchor = date(2026, 4, 1)
    current_anchor = date.today().replace(day=1)
    anchor_delta = (current_anchor.year - fixed_anchor.year) * 12 + (current_anchor.month - fixed_anchor.month)

    relative_expenses: list[dict] = []
    for item in FIXED_MOCK_EXPENSES:
        shifted_item = dict(item)
        shifted_item["date"] = _shift_date_by_months(item["date"], anchor_delta)
        relative_expenses.append(shifted_item)

    relative_prices: list[dict] = []
    for item in FIXED_MOCK_PRICES:
        original_trade_date = datetime.strptime(item["trade_date"], "%Y-%m-%d").date()
        shifted_trade_date = _shift_date_by_months(original_trade_date, anchor_delta)
        shifted_item = dict(item)
        shifted_item["trade_date"] = shifted_trade_date.isoformat()
        relative_prices.append(shifted_item)

    return relative_expenses, relative_prices


def seed(reset: bool = False, relative_dates: bool = False) -> None:
    if reset:
        reset_sqlite_db()
    else:
        init_db()

    mock_expenses, mock_prices = build_demo_dates(relative_dates)

    db = SessionLocal()
    try:
        demo_user = db.query(UserORM).filter(UserORM.email == DEMO_EMAIL).first()
        if not demo_user:
            demo_user = UserORM(email=DEMO_EMAIL, password_hash=get_password_hash(DEMO_PASSWORD))
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

        db.query(ExpenseORM).filter(ExpenseORM.user_id == demo_user.id).delete()
        db.query(BudgetORM).filter(BudgetORM.user_id == demo_user.id).delete()
        db.query(WatchlistORM).filter(WatchlistORM.user_id == demo_user.id).delete()
        db.query(StockPriceORM).filter(StockPriceORM.stock_code.in_([item["stock_code"] for item in mock_prices])).delete(
            synchronize_session=False
        )
        db.commit()

        for item in mock_expenses:
            db.add(ExpenseORM(user_id=demo_user.id, **item))

        for item in MOCK_BUDGETS:
            db.add(BudgetORM(user_id=demo_user.id, **item))

        for item in MOCK_WATCHLIST:
            db.add(
                WatchlistORM(
                    user_id=demo_user.id,
                    price_sync_status="success",
                    last_sync_attempt_at=datetime.now(timezone.utc),
                    **item,
                )
            )

        for item in mock_prices:
            db.add(StockPriceORM(**item))

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
