from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text

from db.database import Base


JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_RETRYING = "retrying"
JOB_STATUS_SUCCESS = "success"
JOB_STATUS_FAILED = "failed"


class SyncJobORM(Base):
    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=JOB_STATUS_PENDING, index=True)
    payload = Column(Text, nullable=False)
    request_id = Column(String(64), nullable=True, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class JobStatusResponse(BaseModel):
    id: int
    job_type: str
    status: Literal["pending", "running", "retrying", "success", "failed"]
    attempts: int
    max_attempts: int
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CreateJobRequest(BaseModel):
    job_type: str = Field(..., min_length=1, max_length=50)
    payload: dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = Field(default=None, max_length=64)
    max_attempts: int = Field(default=3, ge=1, le=3)
