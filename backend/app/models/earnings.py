from sqlalchemy import Column, Float, ForeignKey, Integer, String

from app.database import Base


class Earnings(Base):
    __tablename__ = "earnings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_start = Column(String, nullable=False)  # ISO date, e.g. "2024-01-01"
    week_index = Column(Integer, nullable=False)
    platform = Column(String, nullable=False)
    hours_worked = Column(Float, nullable=False)
    trips_completed = Column(Integer, nullable=False)
    gross_earnings = Column(Float, nullable=False)
    fuel_cost = Column(Float, nullable=False)
    net_earnings = Column(Float, nullable=False)
