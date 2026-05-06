from __future__ import annotations

from datetime import date

from tests.conftest import auth_headers, register_and_login


def test_dashboard_charts_api_returns_expected_sections(client):
    token = register_and_login(client, "charts@example.com")
    today = date.today()
    current_month = today.strftime("%Y-%m")
    current_day = today.strftime("%Y-%m-%d")

    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 5000, "category": "Salary", "type": "income", "date": current_day, "note": "Salary"},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 1200, "category": "Food", "type": "expense", "date": current_day, "note": "Food"},
    )
    client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"month": current_month, "category": "Food", "amount": 2000},
    )

    response = client.get("/api/dashboard/charts", headers=auth_headers(token))
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "monthly_expense_trend",
        "category_distribution",
        "net_income_trend",
        "budget_usage",
    }
    assert payload["monthly_expense_trend"][0]["expense"] == 1200
    assert payload["net_income_trend"][0]["income"] == 5000
    assert payload["budget_usage"][0]["category"] == "Food"
    assert payload["budget_usage"][0]["amount"] == 2000
    assert payload["budget_usage"][0]["usagePercent"] == 60
