from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from app.db.base import Base


class Occurrence(Base):
    __tablename__ = "occurrences"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(String, nullable=False, index=True)
    condition_key = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False)
    state_at_creation = Column(String, nullable=False)

    source_event_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    active = Column(Boolean, nullable=False, default=True)