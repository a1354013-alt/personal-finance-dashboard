from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionORM,
    RecurringTransactionResponse,
    RecurringTransactionUpdate,
)
from models.user import UserORM
from services.auth import get_current_user
from services.recurring_transaction_service import create_recurring_transaction, update_recurring_transaction

router = APIRouter(prefix="/api/recurring-transactions", tags=["Recurring Transactions"])


def _get_owned_item(db: Session, item_id: int, user_id: int) -> RecurringTransactionORM:
    item = (
        db.query(RecurringTransactionORM)
        .filter(RecurringTransactionORM.id == item_id, RecurringTransactionORM.user_id == user_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found.")
    return item


@router.get("", response_model=list[RecurringTransactionResponse])
def list_recurring_transactions(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return (
        db.query(RecurringTransactionORM)
        .filter(RecurringTransactionORM.user_id == current_user.id)
        .order_by(RecurringTransactionORM.is_active.desc(), RecurringTransactionORM.next_run_date.asc(), RecurringTransactionORM.id.desc())
        .all()
    )


@router.post("", response_model=RecurringTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_recurring(
    payload: RecurringTransactionCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    return create_recurring_transaction(db, user_id=current_user.id, payload=payload)


@router.put("/{item_id}", response_model=RecurringTransactionResponse)
def update_recurring(
    item_id: int,
    payload: RecurringTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    item = _get_owned_item(db, item_id, current_user.id)
    return update_recurring_transaction(db, item=item, payload=payload)


@router.patch("/{item_id}/deactivate", response_model=RecurringTransactionResponse)
def deactivate_recurring(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    item = _get_owned_item(db, item_id, current_user.id)
    item.is_active = False
    item.next_run_date = None
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
):
    item = _get_owned_item(db, item_id, current_user.id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
