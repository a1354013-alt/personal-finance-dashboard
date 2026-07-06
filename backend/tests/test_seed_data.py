from __future__ import annotations

from datetime import date

from db.database import SessionLocal
from models.budget import BudgetORM
from models.expense import ExpenseORM
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

    login = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": "demo1234"})
    assert login.status_code == 200
    summary = client.get("/api/dashboard/summary", headers=auth_headers(login.json()["access_token"]))
    assert summary.status_code == 200
    assert summary.json()["budgetItems"]


def test_relative_seed_dates_are_not_double_shifted_or_future_dated():
    expenses, prices = build_demo_dates(relative_dates=True)
    today = date.today()

    assert any(item["date"].year == today.year and item["date"].month == today.month for item in expenses)
    assert all(item["date"] <= today for item in expenses)
    assert all(item["trade_date"] <= today for item in prices)
