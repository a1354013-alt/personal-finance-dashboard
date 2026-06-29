from __future__ import annotations

import pytest

from db.database import SessionLocal
from models.budget import BudgetResponse
from services.budget_summary import build_budget_status


def register_and_login(client, email: str) -> str:
    register_response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert register_response.status_code == 201
    login_response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("category", ["   ", "\n", "\t"])
def test_budget_category_trim_only_rejected(client, category: str):
    token = register_and_login(client, "budget-trim@example.com")
    response = client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"month": "2026-05", "category": category, "amount": 1000},
    )
    assert response.status_code == 422


def test_build_budget_status_matches_budget_response_schema_shape(client):
    token = register_and_login(client, "budget-shape@example.com")

    me = client.get("/api/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    user_id = me.json()["id"]

    create_budget = client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"month": "2026-05", "category": "Food", "amount": 500},
    )
    assert create_budget.status_code in {200, 201}

    expected_keys = set(BudgetResponse.model_fields.keys())

    with SessionLocal() as db:
        items = build_budget_status(db, user_id, "2026-05")

    assert items, "Expected at least one budget status item."
    for item in items:
        assert set(item.keys()) == expected_keys


def test_budget_summary_response_includes_item_id_and_status_flags(client):
    token = register_and_login(client, "budget-summary-flags@example.com")
    headers = auth_headers(token)

    create_budget = client.post(
        "/api/budgets",
        headers=headers,
        json={"month": "2026-05", "category": "Food", "amount": 100},
    )
    assert create_budget.status_code in {200, 201}
    client.post(
        "/api/expenses",
        headers=headers,
        json={"amount": 120, "category": "Food", "type": "expense", "date": "2026-05-15", "note": "Groceries"},
    )

    response = client.get("/api/budgets/summary?month=2026-05", headers=headers)
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["id"] == create_budget.json()["id"]
    assert item["over_budget"] is True
    assert item["warning"] is False


def test_budget_update_requires_amount(client):
    token = register_and_login(client, "budget-update-validation@example.com")
    headers = auth_headers(token)

    create_response = client.post(
        "/api/budgets",
        headers=headers,
        json={"month": "2026-05", "category": "Food", "amount": 100},
    )
    assert create_response.status_code in {200, 201}

    response = client.put(
        f"/api/budgets/{create_response.json()['id']}",
        headers=headers,
        json={},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("month", ["2026-00", "2026-99"])
def test_budget_create_rejects_invalid_month_values(client, month: str):
    token = register_and_login(client, f"budget-invalid-create-{month}@example.com")
    response = client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"month": month, "category": "Food", "amount": 1000},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("path", ["/api/budgets", "/api/budgets/summary"])
@pytest.mark.parametrize("month", ["2026-00", "2026-99"])
def test_budget_query_rejects_invalid_month_values(client, path: str, month: str):
    token = register_and_login(client, f"budget-invalid-query-{path.split('/')[-1]}-{month}@example.com")
    response = client.get(f"{path}?month={month}", headers=auth_headers(token))
    assert response.status_code == 422

