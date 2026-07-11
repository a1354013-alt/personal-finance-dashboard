from __future__ import annotations

from datetime import date as DateType
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer
from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TransactionImportBatchORM(Base):
    __tablename__ = "transaction_import_batches"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    total_rows = Column(Integer, nullable=False, default=0)
    valid_rows = Column(Integer, nullable=False, default=0)
    invalid_rows = Column(Integer, nullable=False, default=0)
    duplicate_rows = Column(Integer, nullable=False, default=0)
    created_rows = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="previewed")
    created_at = Column(DateTime, nullable=False, default=utc_now)
    imported_at = Column(DateTime, nullable=True)

    user = relationship("UserORM", back_populates="transaction_import_batches")
    rows = relationship(
        "TransactionImportRowORM",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="TransactionImportRowORM.source_row_number",
    )


class TransactionImportRowORM(Base):
    __tablename__ = "transaction_import_rows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(36), ForeignKey("transaction_import_batches.id"), nullable=False, index=True)
    source_row_number = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False, default=dict)
    normalized_date = Column(Date, nullable=True)
    normalized_amount = Column(Numeric(18, 2), nullable=True)
    normalized_type = Column(String(10), nullable=True)
    normalized_category = Column(String(50), nullable=True)
    normalized_note = Column(Text, nullable=True)
    payment_method = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="invalid")
    validation_errors = Column(JSON, nullable=False, default=list)
    warnings = Column(JSON, nullable=False, default=list)
    duplicate_reasons = Column(JSON, nullable=False, default=list)
    fingerprint = Column(String(255), nullable=True)
    created_expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)

    batch = relationship("TransactionImportBatchORM", back_populates="rows")


class TransactionImportNormalizedRow(BaseModel):
    transaction_date: Optional[DateType] = None
    amount: Optional[Decimal] = None
    type: Optional[str] = None
    category: str = ""
    description: str = ""
    payment_method: Optional[str] = None
    source_file_name: str
    source_row_number: int
    import_batch_id: str

    @field_serializer("amount")
    def serialize_amount(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None


class TransactionImportPreviewRow(BaseModel):
    id: int
    source_row_number: int
    raw_data: dict[str, Any] = Field(default_factory=dict)
    normalized: TransactionImportNormalizedRow
    status: str
    validation_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duplicate_reasons: list[str] = Field(default_factory=list)
    created_expense_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionImportSummary(BaseModel):
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    warning_rows: int = 0
    rows_to_import: int = 0
    created_rows: int = 0


class TransactionImportBatchResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    created_rows: int
    status: str
    created_at: datetime
    imported_at: Optional[datetime] = None
    summary: TransactionImportSummary

    model_config = ConfigDict(from_attributes=True)


class TransactionImportPreviewResponse(BaseModel):
    batch: TransactionImportBatchResponse
    rows: list[TransactionImportPreviewRow]
    requires_mapping: bool = False
    available_columns: list[str] = Field(default_factory=list)
    suggested_mapping: dict[str, str] = Field(default_factory=dict)
    applied_mapping: dict[str, str] = Field(default_factory=dict)
    missing_required_fields: list[str] = Field(default_factory=list)


class TransactionImportColumnMappingRequest(BaseModel):
    date: Optional[str] = None
    amount: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    note: Optional[str] = None
    payment_method: Optional[str] = None


class TransactionImportConfirmRequest(BaseModel):
    selected_row_numbers: Optional[list[int]] = None


class TransactionImportConfirmResponse(BaseModel):
    batch_id: str
    created_count: int
    skipped_count: int
    duplicate_count: int
    error_count: int
    created_transaction_ids: list[int] = Field(default_factory=list)
