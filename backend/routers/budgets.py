from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.budget import BudgetCreate, BudgetORM, BudgetResponse
from models.user import UserORM
from services.auth import get_current_user
from services.budget_summary import build_budget_status

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.get("", response_model=list[BudgetResponse])
def get_budgets(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return build_budget_status(db, current_user.id)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget: BudgetCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    existing = (
        db.query(BudgetORM)
        .filter(
            BudgetORM.user_id == current_user.id,
            BudgetORM.category == budget.category,
        )
        .first()
    )

    if existing:
        existing.monthly_limit = budget.monthly_limit
        db.commit()
        response.status_code = status.HTTP_200_OK
        return next(item for item in build_budget_status(db, current_user.id) if item["id"] == existing.id)

    new_budget = BudgetORM(
        user_id=current_user.id,
        category=budget.category,
        monthly_limit=budget.monthly_limit,
    )
    db.add(new_budget)
    db.commit()
    return next(item for item in build_budget_status(db, current_user.id) if item["category"] == new_budget.category)


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
