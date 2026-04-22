from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from db.database import Base


class UserORM(Base):
    """User ORM model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    expenses = relationship("ExpenseORM", back_populates="user", cascade="all, delete-orphan")
    watchlist = relationship("WatchlistORM", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("BudgetORM", back_populates="user", cascade="all, delete-orphan")

