from __future__ import annotations

import json
from datetime import datetime, timezone
from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.jobs import get_job_runner
from models.job import JOB_STATUS_PENDING, JOB_STATUS_RETRYING, JOB_STATUS_RUNNING, CreateJobRequest, SyncJobORM

ACTIVE_JOB_STATUSES = (JOB_STATUS_PENDING, JOB_STATUS_RUNNING, JOB_STATUS_RETRYING)


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


def find_active_job_by_payload(
    db: Session,
    *,
    job_type: str,
    expected_payload: Mapping[str, object],
) -> SyncJobORM | None:
    jobs = (
        db.query(SyncJobORM)
        .filter(SyncJobORM.job_type == job_type, SyncJobORM.status.in_(ACTIVE_JOB_STATUSES))
        .order_by(SyncJobORM.created_at.asc())
        .all()
    )
    for job in jobs:
        try:
            payload = json.loads(job.payload)
        except json.JSONDecodeError:
            continue
        if all(payload.get(key) == value for key, value in expected_payload.items()):
            return job
    return None
