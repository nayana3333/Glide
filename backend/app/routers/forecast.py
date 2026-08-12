from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.earnings import Earnings
from app.models.user import User
from app.schemas.forecast import ExplainResponse, ForecastResponse
from app.services import explain_service, forecast_service
from app.services.auth_service import get_current_user, require_self

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


def _earnings_for(db: Session, worker_id: int):
    return (
        db.query(Earnings)
        .filter(Earnings.user_id == worker_id)
        .order_by(Earnings.week_index)
        .all()
    )


@router.get("/{worker_id}", response_model=ForecastResponse)
def get_forecast(
    worker_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_self(worker_id, user)
    rows = _earnings_for(db, worker_id)
    try:
        result = forecast_service.forecast_worker(rows)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return ForecastResponse(worker_id=worker_id, **result)


@router.get("/explain/{worker_id}", response_model=ExplainResponse)
def get_explanation(
    worker_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_self(worker_id, user)
    rows = _earnings_for(db, worker_id)
    target_user = db.query(User).filter(User.id == worker_id).first()
    if target_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Worker not found")
    try:
        result = explain_service.explain_worker(rows, target_user.archetype, target_user.platform)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return ExplainResponse(worker_id=worker_id, **result)
