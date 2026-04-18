from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from app.db import Base


class EventAuditLog(Base):
    __tablename__ = "event_audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(String, nullable=False, unique=True, index=True)
    patient_id = Column(String, nullable=False, index=True)

    logged_at = Column(DateTime(timezone=True), nullable=False)

    validation_status = Column(String, nullable=False)
    validation_reason = Column(String, nullable=True)

    threshold_violated = Column(Boolean, nullable=False, default=False)
    candidate_conditions = Column(JSON, nullable=False, default=list)
    highest_severity = Column(String, nullable=True)
    threshold_reason = Column(String, nullable=True)

    persistence_confirmed = Column(Boolean, nullable=False, default=False)
    persistence_results = Column(JSON, nullable=False, default=list)

    state = Column(String, nullable=True)
    state_transition_from = Column(String, nullable=True)
    state_transition_to = Column(String, nullable=True)

    occurrence_created = Column(Boolean, nullable=False, default=False)
    occurrence_conditions = Column(JSON, nullable=False, default=list)