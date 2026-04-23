from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from app.db.base import Base


class RawEvent(Base):
    __tablename__ = "raw_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, nullable=False, index=True)
    patient_id = Column(String, nullable=False, index=True)

    metric_type = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=False)

    recorded_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)

    device_id = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    battery_level = Column(Integer, nullable=True)
    is_connected = Column(Boolean, nullable=True)

    validation_status = Column(String, nullable=False, default="invalid")
    validation_reason = Column(String, nullable=True)
    delay_seconds = Column(Float, nullable=True)

    raw_json = Column(JSON, nullable=False)