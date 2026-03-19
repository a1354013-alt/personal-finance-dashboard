"""
記帳系統路由 - /api/expenses
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from models.expense import ExpenseORM, ExpenseCreate, ExpenseResponse

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    type: Optional[str] = Query(None, description="篩選類型：income / expense"),
    category: Optional[str] = Query(None, description="篩選類別"),
    db: Session = Depends(get_db),
):
    """取得記帳列表，支援依 type 與 category 篩選"""
    query = db.query(ExpenseORM)
    if type:
        query = query.filter(ExpenseORM.type == type)
    if category:
        query = query.filter(ExpenseORM.category == category)
    return query.order_by(ExpenseORM.date.desc()).all()


@router.post("", response_model=ExpenseResponse, status_code=201)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    """新增一筆收入或支出記錄"""
    record = ExpenseORM(
        amount=payload.amount,
        category=payload.category,
        type=payload.type,
        date=payload.date,
        note=payload.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    """取得單筆記帳記錄"""
    record = db.query(ExpenseORM).filter(ExpenseORM.id == expense_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="記錄不存在")
    return record


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """刪除一筆記帳記錄"""
    record = db.query(ExpenseORM).filter(ExpenseORM.id == expense_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="記錄不存在")
    db.delete(record)
    db.commit()
