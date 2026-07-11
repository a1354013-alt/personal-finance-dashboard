from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.import_batch import (
    TransactionImportConfirmRequest,
    TransactionImportConfirmResponse,
    TransactionImportBatchResponse,
    TransactionImportColumnMappingRequest,
    TransactionImportPreviewResponse,
)
from models.user import UserORM
from services.auth import get_current_user
from services.transaction_import_service import (
    confirm_transaction_import,
    get_import_batch_detail,
    list_import_batches,
    preview_transaction_import,
)

router = APIRouter(prefix="/api/imports/transactions", tags=["Transaction Imports"])


@router.post("/preview", response_model=TransactionImportPreviewResponse, status_code=status.HTTP_201_CREATED)
async def preview_import(
    file: UploadFile = File(...),
    column_mapping: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    mapping_payload = None
    if column_mapping:
        try:
            mapping_payload = TransactionImportColumnMappingRequest.model_validate(json.loads(column_mapping))
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="Invalid column mapping payload.") from exc
    content = await file.read()
    return preview_transaction_import(
        db,
        user=current_user,
        file_name=file.filename or "upload",
        content=content,
        column_mapping=mapping_payload,
    )


@router.post("/{batch_id}/confirm", response_model=TransactionImportConfirmResponse)
def confirm_import(
    batch_id: str,
    payload: TransactionImportConfirmRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return confirm_transaction_import(
        db,
        user=current_user,
        batch_id=batch_id,
        selected_row_numbers=payload.selected_row_numbers,
    )


@router.get("", response_model=list[TransactionImportBatchResponse])
def get_import_batches(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return list_import_batches(db, user=current_user)


@router.get("/{batch_id}", response_model=TransactionImportPreviewResponse)
def get_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return get_import_batch_detail(db, batch_id=batch_id, user=current_user)
