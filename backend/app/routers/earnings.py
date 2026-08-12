from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.earnings import Earnings
from app.models.user import User
from app.schemas.earnings import EarningsCreate, EarningsResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/earnings", tags=["earnings"])


@router.post("", response_model=EarningsResponse)
def add_earnings(
    payload: EarningsCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    count = db.query(Earnings).filter(Earnings.user_id == user.id).count()
    row = Earnings(
        user_id=user.id,
        week_start=payload.week_start,
        week_index=count,
        platform=payload.platform,
        hours_worked=payload.hours_worked,
        trips_completed=payload.trips_completed,
        gross_earnings=payload.gross_earnings,
        fuel_cost=payload.fuel_cost,
        net_earnings=max(payload.gross_earnings - payload.fuel_cost, 0.0),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{worker_id}", response_model=list[EarningsResponse])
def list_earnings(
    worker_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Earnings)
        .filter(Earnings.user_id == worker_id)
        .order_by(Earnings.week_index)
        .all()
    )
