from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.earnings import Earnings
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services import buffer_service, forecast_service
from app.services.auth_service import get_current_user, require_self

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{worker_id}", response_model=DashboardResponse)
def get_dashboard(
    worker_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_self(worker_id, user)
    rows = (
        db.query(Earnings)
        .filter(Earnings.user_id == worker_id)
        .order_by(Earnings.week_index)
        .all()
    )

    next_week = None
    if len(rows) >= forecast_service.MIN_HISTORY_WEEKS:
        forecast = forecast_service.forecast_worker(rows, horizon=1)
        next_week = forecast["forecast"][0]

    balance = buffer_service.get_balance(db, worker_id)

    latest_alert = (
        db.query(Alert)
        .filter(Alert.user_id == worker_id)
        .order_by(Alert.week_start.desc())
        .first()
    )

    return DashboardResponse(
        worker_id=worker_id,
        recent_earnings=rows[-8:],
        next_week_forecast=next_week,
        buffer_balance=balance,
        latest_alert_message=latest_alert.message if latest_alert else None,
    )
