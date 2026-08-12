from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.buffer import BufferAmount, BufferStateResponse, BufferTransactionResponse
from app.services import buffer_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/buffer", tags=["buffer"])


@router.get("/{worker_id}", response_model=BufferStateResponse)
def get_buffer(
    worker_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    balance, transactions = buffer_service.get_state(db, worker_id)
    return BufferStateResponse(balance=balance, transactions=transactions)


@router.post("/deposit", response_model=BufferTransactionResponse)
def deposit(
    payload: BufferAmount,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return buffer_service.manual_deposit(db, user.id, payload.amount)


@router.post("/withdraw", response_model=BufferTransactionResponse)
def withdraw(
    payload: BufferAmount,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return buffer_service.manual_withdraw(db, user.id, payload.amount)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
