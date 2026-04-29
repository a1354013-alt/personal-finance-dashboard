from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.jobs import get_job_runner
from models.job import JOB_STATUS_PENDING, CreateJobRequest, SyncJobORM


def create_job(db: Session, request: CreateJobRequest) -> SyncJobORM:
    now = datetime.now(timezone.utc)
    job = SyncJobORM(
        job_type=request.job_type,
        status=JOB_STATUS_PENDING,
        payload=json.dumps(request.payload, ensure_ascii=False),
        request_id=request.request_id,
        max_attempts=request.max_attempts,
        attempts=0,
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    get_job_runner().enqueue(job.id)
    return job
