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
        items = build_budget_status(db, user_id)

    assert items, "Expected at least one budget status item."
    for item in items:
        assert set(item.keys()) == expected_keys

