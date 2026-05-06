from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from db.database import get_db
from models.report import MONTH_PATTERN
from models.user import UserORM
from services.auth import get_current_user
from services.report_service import build_monthly_report, render_monthly_report_csv, render_monthly_report_pdf

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/monthly")
def export_monthly_report(
    month: str = Query(..., pattern=MONTH_PATTERN),
    format: str = Query(...),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    normalized_format = format.strip().lower()
    if normalized_format not in {"csv", "pdf"}:
        raise HTTPException(status_code=422, detail="format must be either csv or pdf.")

    report = build_monthly_report(db=db, user_id=current_user.id, month=month)
    filename = f"finance-report-{month}.{normalized_format}"
    if normalized_format == "csv":
        content = render_monthly_report_csv(report)
        media_type = "text/csv; charset=utf-8"
    else:
        content = render_monthly_report_pdf(report)
        media_type = "application/pdf"

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)
