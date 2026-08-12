from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    week_start: str
    level: str
    predicted_income: float
    rolling_avg: float
    message: str

    class Config:
        from_attributes = True
