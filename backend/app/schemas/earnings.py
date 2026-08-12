from pydantic import BaseModel


class EarningsCreate(BaseModel):
    week_start: str
    platform: str
    hours_worked: float
    trips_completed: int
    gross_earnings: float
    fuel_cost: float


class EarningsResponse(BaseModel):
    id: int
    week_start: str
    week_index: int
    platform: str
    hours_worked: float
    trips_completed: int
    gross_earnings: float
    fuel_cost: float
    net_earnings: float

    class Config:
        from_attributes = True
