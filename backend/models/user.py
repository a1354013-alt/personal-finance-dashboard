"""
使用者資料模型
定義使用者實體與認證相關模型。
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.database import Base

class UserORM(Base):
    """使用者資料表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 建立與其他資料表的關聯
    expenses = relationship("ExpenseORM", back_populates="user", cascade="all, delete-orphan")
    watchlist = relationship("WatchlistORM", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("BudgetORM", back_populates="user", cascade="all, delete-orphan")
