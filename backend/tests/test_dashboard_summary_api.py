from __future__ import annotations
from datetime import date
from tests.conftest import auth_headers, register_and_login


def test_dashboard_summary_api_empty_state(client):
    token = register_and_login(client, "empty@example.com")
    response = client.get("/api/dashboard/summary", headers=auth_headers(token))
    assert response.status_code == 200
    payload = response.json()
    
    assert payload["monthlyIncome"] == 0
    assert payload["monthlyExpense"] == 0
    assert payload["monthlyBalance"] == 0
    assert payload["topExpenseCategory"] is None
    assert len(payload["monthlyTrend"]) == 6
    assert all(item["income"] == 0 for item in payload["monthlyTrend"])
    assert len(payload["expenseByCategory"]) == 0
    assert len(payload["recentTransactions"]) == 0
    assert payload["totalBudget"] == 0
    assert payload["totalUsed"] == 0
    assert payload["totalRemaining"] == 0
    assert payload["budgetOverCount"] == 0
    assert payload["budgetWarningCount"] == 0
    assert payload["budgetItems"] == []


def test_dashboard_summary_api_with_data(client):
    token = register_and_login(client, "data@example.com")
    today = date.today()
    current_month = today.strftime("%Y-%m")
    
    # Current month data
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 10000, "category": "Salary", "type": "income", "date": today.strftime("%Y-%m-%d")},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 2000, "category": "Food", "type": "expense", "date": today.strftime("%Y-%m-%d")},
    )
    client.post(
        "/api/expenses",
        headers=auth_headers(token),
        json={"amount": 3000, "category": "Housing", "type": "expense", "date": today.strftime("%Y-%m-%d")},
    )
    client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"month": current_month, "category": "Food", "amount": 2500},
    )
    client.post(
        "/api/budgets",
        headers=auth_headers(token),
        json={"month": current_month, "category": "Housing", "amount": 2800},
    )
    
    response = client.get("/api/dashboard/summary", headers=auth_headers(token))
    assert response.status_code == 200
    payload = response.json()
    
    assert payload["monthlyIncome"] == 10000
    assert payload["monthlyExpense"] == 5000
    assert payload["monthlyBalance"] == 5000
    assert payload["topExpenseCategory"] == "Housing"
    assert len(payload["expenseByCategory"]) == 2
    assert payload["expenseByCategory"][0]["category"] == "Housing"
    assert payload["expenseByCategory"][0]["amount"] == 3000
    assert len(payload["recentTransactions"]) == 3
    assert payload["recentTransactions"][0]["category"] == "Housing"
    assert payload["totalBudget"] == 5300
    assert payload["totalUsed"] == 5000
    assert payload["totalRemaining"] == 300
    assert payload["budgetOverCount"] == 1
    assert payload["budgetWarningCount"] == 1
    assert payload["budgetItems"][0]["category"] == "Housing"
    assert payload["budgetItems"][0]["amount"] == 2800
    assert payload["budgetItems"][0]["used"] == 3000
    assert payload["budgetItems"][0]["usagePercent"] > 100


def test_dashboard_summary_user_isolation(client):
    token1 = register_and_login(client, "user1@example.com")
    token2 = register_and_login(client, "user2@example.com")
    today = date.today().strftime("%Y-%m-%d")
    
    # User 1 adds data
    client.post(
        "/api/expenses",
        headers=auth_headers(token1),
        json={"amount": 5000, "category": "Salary", "type": "income", "date": today},
    )
    
    # User 2 should still have 0
    response = client.get("/api/dashboard/summary", headers=auth_headers(token2))
    assert response.json()["monthlyIncome"] == 0
    
    # User 1 should have 5000
    response = client.get("/api/dashboard/summary", headers=auth_headers(token1))
    assert response.json()["monthlyIncome"] == 5000
