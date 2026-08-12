from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.earnings import Earnings
from app.models.user import User
from app.schemas.alert import AlertResponse
from app.services import forecast_service
from app.services.auth_service import get_current_user, require_self

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

MESSAGES = {
    "RED": "Predicted low-income week ahead ({ratio:.0%} below your recent average) — consider trimming discretionary spend.",
    "AMBER": "Slightly below your recent average expected ({ratio:.0%}) — keep an eye on it.",
    "GREEN": "Income expected to stay near your recent average.",
}


@router.get("/{worker_id}", response_model=list[AlertResponse])
def get_alerts(
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
    try:
        forecast = forecast_service.forecast_worker(rows)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    existing_weeks = {
        a.week_start
        for a in db.query(Alert).filter(Alert.user_id == worker_id).all()
    }

    for week in forecast["forecast"]:
        if week["dip_level"] == "GREEN" or week["week_start"] in existing_weeks:
            continue
        db.add(
            Alert(
                user_id=worker_id,
                week_start=week["week_start"],
                level=week["dip_level"],
                predicted_income=week["yhat"],
                rolling_avg=forecast["rolling_avg"],
                message=MESSAGES[week["dip_level"]].format(ratio=week["deficit_ratio"]),
            )
        )
    db.commit()

    return (
        db.query(Alert)
        .filter(Alert.user_id == worker_id)
        .order_by(Alert.week_start.desc())
        .all()
    )
