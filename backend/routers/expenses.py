from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.expense import ExpenseCreate, ExpenseORM, ExpenseResponse
from models.user import UserORM
from services.auth import get_current_user

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.get("", response_model=list[ExpenseResponse])
def get_expenses(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    query = db.query(ExpenseORM).filter(ExpenseORM.user_id == current_user.id)
    if type:
        query = query.filter(ExpenseORM.type == type)
    return query.order_by(ExpenseORM.date.desc(), ExpenseORM.id.desc()).all()


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    expense = ExpenseORM(
        user_id=current_user.id,
        amount=payload.amount,
        category=payload.category,
        type=payload.type,
        date=payload.date,
        note=payload.note,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    expense = (
        db.query(ExpenseORM)
        .filter(ExpenseORM.id == expense_id, ExpenseORM.user_id == current_user.id)
        .first()
    )
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")

    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted."}
