from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import UserORM
from models.budget import BudgetORM, BudgetCreate, BudgetResponse
from models.expense import ExpenseORM
from services.auth import get_current_user
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])

@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """取得使用者所有預算，並計算當月使用率 (v0.6.0)"""
    budgets = db.query(BudgetORM).filter(BudgetORM.user_id == current_user.id).all()
    
    # 計算當月各類別總支出
    now = datetime.now()
    first_day = datetime(now.year, now.month, 1)
    
    results = []
    for budget in budgets:
        # 取得當月該類別的總支出
        spent = db.query(ExpenseORM).filter(
            ExpenseORM.user_id == current_user.id,
            ExpenseORM.category == budget.category,
            ExpenseORM.date >= first_day.date()
        ).all()
        
        total_spent = sum(item.amount for item in spent)
        
        # 轉換為 Response 並加入計算欄位
        res = BudgetResponse.from_orm(budget)
        res.current_spent = total_spent
        res.percent_used = (total_spent / budget.monthly_limit) * 100 if budget.monthly_limit > 0 else 0
        results.append(res)
        
    return results

@router.post("/", response_model=BudgetResponse)
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """新增預算設定 (v0.6.0)"""
    # 檢查是否已存在同類別預算
    existing = db.query(BudgetORM).filter(
        BudgetORM.user_id == current_user.id,
        BudgetORM.category == budget.category
    ).first()
    
    if existing:
        # 如果存在則更新
        existing.monthly_limit = budget.monthly_limit
        db.commit()
        db.refresh(existing)
        return existing

    new_budget = BudgetORM(
        user_id=current_user.id,
        category=budget.category,
        monthly_limit=budget.monthly_limit
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user)
):
    """刪除預算設定 (v0.6.0)"""
    budget = db.query(BudgetORM).filter(
        BudgetORM.id == budget_id,
        BudgetORM.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="預算設定不存在")
        
    db.delete(budget)
    db.commit()
    return None
