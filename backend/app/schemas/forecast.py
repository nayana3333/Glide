from pydantic import BaseModel


class ForecastWeek(BaseModel):
    week_start: str
    yhat: float
    yhat_lower: float | None
    yhat_upper: float | None
    dip_level: str  # GREEN | AMBER | RED
    deficit_ratio: float


class ForecastResponse(BaseModel):
    worker_id: int
    model_used: str
    rolling_avg: float
    forecast: list[ForecastWeek]


class ExplainResponse(BaseModel):
    worker_id: int
    predicted: float
    rolling_avg_4wk: float
    deficit_ratio: float
    contributions: dict[str, float]
