from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from models.dashboard import DashboardSummaryResponse
from models.user import UserORM
from services.auth import get_current_user
from services.dashboard_service import build_dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return build_dashboard_summary(db=db, user_id=current_user.id)
