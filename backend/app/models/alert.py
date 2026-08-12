from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_start = Column(String, nullable=False)
    level = Column(String, nullable=False)  # GREEN | AMBER | RED
    predicted_income = Column(Float, nullable=False)
    rolling_avg = Column(Float, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
