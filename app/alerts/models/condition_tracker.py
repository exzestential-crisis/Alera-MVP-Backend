from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from app.db.base import Base


class ConditionTracker(Base):
    __tablename__ = "condition_trackers"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(String, nullable=False, index=True)
    condition_key = Column(String, nullable=False, index=True)

    active = Column(Boolean, nullable=False, default=True)

    started_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)

    duration_seconds = Column(Float, nullable=False, default=0.0)
    confirmed = Column(Boolean, nullable=False, default=False)