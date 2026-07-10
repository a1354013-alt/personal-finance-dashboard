from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

from db.database import SessionLocal
from models.recurring_transaction import RecurringTransactionORM
from tests.conftest import auth_headers, register_and_login


def _current_month_dates() -> tuple[str, str]:
    today = date.today()
    first = today.replace(day=1).isoformat()
    current_month_date = date(today.year, today.month, min(today.day, monthrange(today.year, today.month)[1])).isoformat()
    return first, current_month_date


def test_monthly_forecast_without_recurring_transactions(client):
    token = register_and_login(client, "forecast-empty-recurring@example.com")
    first, _future = _current_month_dates()
    client.post("/api/expenses", headers=auth_headers(token), json={"amount": 1000, "category": "Salary", "type": "income", "date": first})
    client.post("/api/expenses", headers=auth_headers(token), json={"amount": 300, "category": "Food", "type": "expense", "date": first})

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))
    forecast = response.json()["monthlyForecast"]

    assert forecast["actualIncomeToDate"] == 1000
    assert forecast["actualExpenseToDate"] == 300
    assert forecast["recurringIncomePending"] == 0
    assert forecast["recurringExpensePending"] == 0
    assert forecast["projectedBalance"] == 700


def test_monthly_forecast_with_monthly_recurring_income(client):
    token = register_and_login(client, "forecast-income@example.com")
    _first, future = _current_month_dates()
    client.post(
        "/api/recurring-transactions",
        headers=auth_headers(token),
        json={"amount": 2500, "category": "Salary", "type": "income", "frequency": "monthly", "start_date": future},
    )

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))
    forecast = response.json()["monthlyForecast"]

    assert forecast["recurringIncomePending"] == 2500
    assert forecast["projectedIncome"] == 2500


def test_monthly_forecast_with_monthly_recurring_expense(client):
    token = register_and_login(client, "forecast-expense@example.com")
    _first, future = _current_month_dates()
    client.post(
        "/api/recurring-transactions",
        headers=auth_headers(token),
        json={"amount": 800, "category": "Utilities", "type": "expense", "frequency": "monthly", "start_date": future},
    )

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))
    forecast = response.json()["monthlyForecast"]

    assert forecast["recurringExpensePending"] == 800
    assert forecast["projectedExpense"] == 800


def test_monthly_forecast_ignores_inactive_recurring_transactions(client):
    token = register_and_login(client, "forecast-inactive@example.com")
    _first, future = _current_month_dates()
    created = client.post(
        "/api/recurring-transactions",
        headers=auth_headers(token),
        json={"amount": 800, "category": "Utilities", "type": "expense", "frequency": "monthly", "start_date": future},
    ).json()
    client.patch(f"/api/recurring-transactions/{created['id']}/deactivate", headers=auth_headers(token))

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))

    assert response.json()["monthlyForecast"]["recurringExpensePending"] == 0


def test_monthly_forecast_user_scoping(client):
    token = register_and_login(client, "forecast-scope@example.com")
    other_token = register_and_login(client, "forecast-scope-other@example.com")
    _first, future = _current_month_dates()
    client.post(
        "/api/recurring-transactions",
        headers=auth_headers(other_token),
        json={"amount": 999, "category": "Salary", "type": "income", "frequency": "monthly", "start_date": future},
    )

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))

    assert response.json()["monthlyForecast"]["recurringIncomePending"] == 0


def test_monthly_forecast_derives_missing_next_run_date_for_active_recurring(client):
    token = register_and_login(client, "forecast-derived-next-run@example.com")
    user_response = client.post(
        "/api/auth/login",
        json={"email": "forecast-derived-next-run@example.com", "password": "password123"},
    )
    user_id = user_response.json()["user"]["id"]
    today = date.today()

    with SessionLocal() as db:
        db.add(
            RecurringTransactionORM(
                user_id=user_id,
                amount=1500,
                category="Salary",
                type="income",
                note="Derived schedule",
                frequency="monthly",
                start_date=today,
                end_date=None,
                next_run_date=None,
                is_active=True,
            )
        )
        db.commit()

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))

    assert response.json()["monthlyForecast"]["recurringIncomePending"] == 1500


def test_monthly_forecast_excludes_ended_recurring_without_future_run_date(client):
    token = register_and_login(client, "forecast-ended-derived@example.com")
    user_response = client.post(
        "/api/auth/login",
        json={"email": "forecast-ended-derived@example.com", "password": "password123"},
    )
    user_id = user_response.json()["user"]["id"]
    today = date.today()
    ended_day = max(1, today.day - 1)
    ended_date = today.replace(day=ended_day)

    with SessionLocal() as db:
        db.add(
            RecurringTransactionORM(
                user_id=user_id,
                amount=700,
                category="Utilities",
                type="expense",
                note="Expired schedule",
                frequency="monthly",
                start_date=today.replace(day=1),
                end_date=ended_date,
                next_run_date=None,
                is_active=True,
            )
        )
        db.commit()

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))

    assert response.json()["monthlyForecast"]["recurringExpensePending"] == 0


def test_unbudgeted_spending_excludes_categories_with_budgets(client):
    token = register_and_login(client, "unbudgeted-exclude@example.com")
    today = date.today()
    month = today.strftime("%Y-%m")
    client.post("/api/expenses", headers=auth_headers(token), json={"amount": 300, "category": "Food", "type": "expense", "date": today.isoformat()})
    client.post("/api/budgets", headers=auth_headers(token), json={"month": month, "category": "Food", "amount": 500})

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))

    assert response.json()["unbudgetedSpending"] == []


def test_unbudgeted_spending_includes_categories_without_budgets(client):
    token = register_and_login(client, "unbudgeted-include@example.com")
    today = date.today()
    client.post("/api/expenses", headers=auth_headers(token), json={"amount": 300, "category": "Travel", "type": "expense", "date": today.isoformat()})
    client.post("/api/expenses", headers=auth_headers(token), json={"amount": 100, "category": "Travel", "type": "expense", "date": today.isoformat()})

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))
    item = response.json()["unbudgetedSpending"][0]

    assert item["category"] == "Travel"
    assert item["amount"] == 400
    assert item["transactionCount"] == 2


def test_unbudgeted_spending_only_current_month(client):
    token = register_and_login(client, "unbudgeted-current-month@example.com")
    last_month = (date.today().replace(day=1) - timedelta(days=1)).isoformat()
    client.post("/api/expenses", headers=auth_headers(token), json={"amount": 300, "category": "Travel", "type": "expense", "date": last_month})

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))

    assert response.json()["unbudgetedSpending"] == []


def test_unbudgeted_spending_user_scoping(client):
    token = register_and_login(client, "unbudgeted-scope@example.com")
    other_token = register_and_login(client, "unbudgeted-scope-other@example.com")
    today = date.today().isoformat()
    client.post("/api/expenses", headers=auth_headers(other_token), json={"amount": 300, "category": "Travel", "type": "expense", "date": today})

    response = client.get("/api/dashboard/summary", headers=auth_headers(token))

    assert response.json()["unbudgetedSpending"] == []
