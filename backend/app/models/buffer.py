from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.database import Base


class BufferTransaction(Base):
    __tablename__ = "buffer_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_start = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # auto_save | auto_release | manual_deposit | manual_withdraw
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
