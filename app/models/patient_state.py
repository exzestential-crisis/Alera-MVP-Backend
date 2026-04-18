from sqlalchemy import Column, Integer, String, DateTime
from app.db import Base


class PatientState(Base):
    __tablename__ = "patient_states"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(String, nullable=False, unique=True)

    current_state = Column(String, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), nullable=False)