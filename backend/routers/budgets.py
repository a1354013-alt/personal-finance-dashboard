from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.budget import BudgetCreate, BudgetORM, BudgetResponse, BudgetSummaryResponse, BudgetUpdate
from models.user import UserORM
from services.auth import get_current_user
from services.budget_summary import build_budget_status, build_budget_summary

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.get("", response_model=list[BudgetResponse])
def get_budgets(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    if not month:
        month = date.today().strftime("%Y-%m")
    return build_budget_status(db, current_user.id, month)


@router.get("/summary", response_model=BudgetSummaryResponse)
def get_budget_summary(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    if not month:
        month = date.today().strftime("%Y-%m")
    return build_budget_summary(db, current_user.id, month)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_budget(
    budget: BudgetCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    existing = (
        db.query(BudgetORM)
        .filter(
            BudgetORM.user_id == current_user.id,
            BudgetORM.month == budget.month,
            BudgetORM.category == budget.category,
        )
        .first()
    )

    if existing:
        existing.amount = budget.amount
        db.commit()
        response.status_code = status.HTTP_200_OK
        return next(item for item in build_budget_status(db, current_user.id, budget.month) if item["category"] == existing.category)

    new_budget = BudgetORM(
        user_id=current_user.id,
        month=budget.month,
        category=budget.category,
        amount=budget.amount,
    )
    db.add(new_budget)
    db.commit()
    return next(item for item in build_budget_status(db, current_user.id, budget.month) if item["category"] == new_budget.category)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_update: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    budget = (
        db.query(BudgetORM)
        .filter(BudgetORM.id == budget_id, BudgetORM.user_id == current_user.id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")

    if budget_update.category is not None:
        budget.category = budget_update.category
    if budget_update.amount is not None:
        budget.amount = budget_update.amount
    
    db.commit()
    return next(item for item in build_budget_status(db, current_user.id, budget.month) if item["category"] == budget.category)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    budget = (
        db.query(BudgetORM)
        .filter(BudgetORM.id == budget_id, BudgetORM.user_id == current_user.id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")

    db.delete(budget)
    db.commit()
