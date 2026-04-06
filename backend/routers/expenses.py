"""
記帳系統路由 - /api/expenses
提供收入與支出的 CRUD 操作，具備使用者資料隔離。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from db.database import get_db
from models.expense import ExpenseORM, ExpenseCreate, ExpenseResponse
from models.user import UserORM
from services.auth import get_current_user

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.get("", response_model=List[ExpenseResponse])
def get_expenses(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
): # 確保用戶隔離
    """取得當前使用者的記帳清單"""
    query = db.query(ExpenseORM).filter(ExpenseORM.user_id == current_user.id)
    if type:
        query = query.filter(ExpenseORM.type == type)
    return query.order_by(ExpenseORM.date.desc()).all()


@router.post("", response_model=ExpenseResponse)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
): # 確保用戶隔離
    """建立新的記帳記錄"""
    new_expense = ExpenseORM(
        user_id=current_user.id,
        amount=payload.amount,
        category=payload.category,
        type=payload.type,
        date=payload.date,
        note=payload.note
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
): # 確保用戶隔離
    """刪除指定的記帳記錄"""
    expense = db.query(ExpenseORM).filter(
        ExpenseORM.id == expense_id,
        ExpenseORM.user_id == current_user.id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="找不到該筆記錄")
    
    db.delete(expense)
    db.commit()
    return {"message": "刪除成功"}
