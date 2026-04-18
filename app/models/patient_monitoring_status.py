from sqlalchemy import Column, Integer, String, DateTime
from app.db import Base


class PatientMonitoringStatus(Base):
    __tablename__ = "patient_monitoring_status"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, nullable=False, unique=True, index=True)
    last_valid_realtime_event_at = Column(DateTime(timezone=True), nullable=True)