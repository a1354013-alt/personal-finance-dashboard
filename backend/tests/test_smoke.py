from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DB_PATH = ROOT / "test_smoke.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ENV"] = "development"

from db.database import engine, init_db, reset_sqlite_db  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    reset_sqlite_db()
    init_db()
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def register_and_login(email: str):
    register_response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_auth_register_login_me():
    token = register_and_login("smoke@example.com")

    me_response = client.get("/api/auth/me", headers=auth_headers(token))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "smoke@example.com"


def test_expenses_create_list_delete_with_user_isolation():
    token_a = register_and_login("user-a@example.com")
    token_b = register_and_login("user-b@example.com")

    create_response = client.post(
        "/api/expenses",
        headers=auth_headers(token_a),
        json={"amount": 123.45, "category": "Food", "type": "expense", "date": "2026-04-10", "note": "Lunch"},
    )
    assert create_response.status_code == 201
    expense_id = create_response.json()["id"]

    list_a = client.get("/api/expenses", headers=auth_headers(token_a))
    list_b = client.get("/api/expenses", headers=auth_headers(token_b))
    assert len(list_a.json()) == 1
    assert list_b.json() == []

    delete_other_user = client.delete(f"/api/expenses/{expense_id}", headers=auth_headers(token_b))
    assert delete_other_user.status_code == 404

    delete_response = client.delete(f"/api/expenses/{expense_id}", headers=auth_headers(token_a))
    assert delete_response.status_code == 200


def test_budgets_create_list_delete_and_dashboard_summary():
    token = register_and_login("budget@example.com")

    create_budget = client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"category": "Food", "monthly_limit": 1000},
    )
    assert create_budget.status_code == 201
    budget_id = create_budget.json()["id"]

    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 3000, "category": "Salary", "type": "income", "date": "2026-04-01", "note": "Salary"},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 700, "category": "Food", "type": "expense", "date": "2026-04-05", "note": "Groceries"},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 600, "category": "Food", "type": "expense", "date": "2026-05-01", "note": "Next month"},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 200, "category": "Food", "type": "income", "date": "2026-04-06", "note": "Refund"},
    )

    budgets_response = client.get("/api/budgets", headers=auth_headers(token))
    assert budgets_response.status_code == 200
    budgets = budgets_response.json()
    assert budgets[0]["current_spent"] == 700
    assert budgets[0]["percent_used"] == 70

    dashboard_response = client.get("/api/dashboard/summary", headers=auth_headers(token))
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["total_income"] == 3200
    assert dashboard["total_expense"] == 1300
    assert dashboard["over_budget"] == []

    advice_response = client.get("/api/ai/budget-advice", headers=auth_headers(token))
    assert advice_response.status_code == 200
    assert advice_response.json()["budget_status"][0]["current_spent"] == 700

    delete_budget = client.delete(f"/api/budgets/{budget_id}", headers=auth_headers(token))
    assert delete_budget.status_code == 204
