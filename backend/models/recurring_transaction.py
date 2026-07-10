from __future__ import annotations

from datetime import date as DateType, datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_serializer, field_validator, model_validator
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from db.database import Base


FREQUENCIES = {"weekly", "monthly", "yearly"}
TRANSACTION_TYPES = {"income", "expense"}


class RecurringTransactionORM(Base):
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    category = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)
    note = Column(Text, nullable=True)
    frequency = Column(String(10), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    next_run_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("UserORM", back_populates="recurring_transactions")


class RecurringTransactionBase(BaseModel):
    amount: Decimal
    category: str
    type: str
    note: Optional[str] = None
    frequency: str
    start_date: DateType
    end_date: Optional[DateType] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("amount must be greater than 0.")
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        category = value.strip()
        if not category:
            raise ValueError("category is required.")
        if len(category) > 50:
            raise ValueError("category must be 50 characters or fewer.")
        return category

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in TRANSACTION_TYPES:
            raise ValueError("type must be either 'income' or 'expense'.")
        return value

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, value: str) -> str:
        if value not in FREQUENCIES:
            raise ValueError("frequency must be weekly, monthly, or yearly.")
        return value

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        note = value.strip()
        return note or None

    @model_validator(mode="after")
    def validate_dates(self) -> "RecurringTransactionBase":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class RecurringTransactionCreate(RecurringTransactionBase):
    pass


class RecurringTransactionUpdate(RecurringTransactionBase):
    is_active: bool = True


class RecurringTransactionResponse(RecurringTransactionBase):
    id: int
    next_run_date: Optional[DateType] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> float:
        return float(value)
