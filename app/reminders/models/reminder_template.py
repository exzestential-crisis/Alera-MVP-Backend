from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.sql import func

from app.db.base import Base
from app.reminders.enums import RecurrenceType, ReminderCategory


class ReminderTemplate(Base):
    __tablename__ = "reminder_templates"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, nullable=False, index=True)
    created_by = Column(String, nullable=False, index=True)

    category = Column(Enum(ReminderCategory), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    recurrence_type = Column(Enum(RecurrenceType), nullable=False)
    recurrence_rule = Column(Text, nullable=True)  # JSON/text later if needed

    default_time = Column(String, nullable=False)  # "10:30:00"
    timezone = Column(String, nullable=False, default="UTC")

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)