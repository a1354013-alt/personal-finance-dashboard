import pytest
from datetime import date
from decimal import Decimal
from fastapi import status
from models.budget import BudgetORM
from models.expense import ExpenseORM
from db.database import SessionLocal
from tests.conftest import register_and_login, auth_headers

def test_budget_summary_logic(client):
    email = "budget_test@example.com"
    token = register_and_login(client, email)
    headers = auth_headers(token)
    
    db = SessionLocal()
    from models.user import UserORM
    user = db.query(UserORM).filter(UserORM.email == email).first()
    user_id = user.id
    
    # Setup: Create some expenses for May 2026
    month = "2026-05"
    db.add(ExpenseORM(
        user_id=user_id,
        amount=5000,
        category="Food",
        type="expense",
        date=date(2026, 5, 10)
    ))
    db.add(ExpenseORM(
        user_id=user_id,
        amount=12000,
        category="Housing",
        type="expense",
        date=date(2026, 5, 1)
    ))
    # Income should be ignored in budget summary
    db.add(ExpenseORM(
        user_id=user_id,
        amount=50000,
        category="Salary",
        type="income",
        date=date(2026, 5, 5)
    ))
    
    # Setup: Create budgets
    db.add(BudgetORM(
        user_id=user_id,
        month=month,
        category="Food",
        amount=6000
    ))
    db.add(BudgetORM(
        user_id=user_id,
        month=month,
        category="Housing",
        amount=10000
    ))
    db.commit()
    
    # Test: Get summary
    response = client.get(f"/api/budgets/summary?month={month}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["month"] == month
    assert data["totalBudget"] == 16000
    assert data["totalUsed"] == 17000
    assert data["totalRemaining"] == -1000
    
    items = {item["category"]: item for item in data["items"]}
    
    # Food: 5000 used out of 6000 (83.3%) -> warning
    assert items["Food"]["budget"] == 6000
    assert items["Food"]["used"] == 5000
    assert items["Food"]["status"] == "warning"
    
    # Housing: 12000 used out of 10000 (120%) -> over
    assert items["Housing"]["budget"] == 10000
    assert items["Housing"]["used"] == 12000
    assert items["Housing"]["status"] == "over"
    db.close()

def test_budget_month_isolation(client):
    email = "month_test@example.com"
    token = register_and_login(client, email)
    headers = auth_headers(token)
    
    db = SessionLocal()
    from models.user import UserORM
    user = db.query(UserORM).filter(UserORM.email == email).first()
    
    # Budget for May
    db.add(BudgetORM(
        user_id=user.id,
        month="2026-05",
        category="Food",
        amount=5000
    ))
    db.commit()
    
    # Query June
    response = client.get("/api/budgets/summary?month=2026-06", headers=headers)
    data = response.json()
    assert len(data["items"]) == 0
    assert data["totalBudget"] == 0
    db.close()

def test_budget_crud(client):
    token = register_and_login(client, "crud_test@example.com")
    headers = auth_headers(token)
    
    # Create
    payload = {"month": "2026-07", "category": "Travel", "amount": 20000}
    response = client.post("/api/budgets", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    budget_id = response.json()["id"]
    
    # Update
    update_payload = {"amount": 25000}
    response = client.put(f"/api/budgets/{budget_id}", json=update_payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["amount"] == 25000
    
    # Delete
    response = client.delete(f"/api/budgets/{budget_id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
