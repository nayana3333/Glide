from app.schemas.earnings import EarningsResponse
from app.schemas.forecast import ForecastWeek
from pydantic import BaseModel


class DashboardResponse(BaseModel):
    worker_id: int
    recent_earnings: list[EarningsResponse]
    next_week_forecast: ForecastWeek | None
    buffer_balance: float
    latest_alert_message: str | None
