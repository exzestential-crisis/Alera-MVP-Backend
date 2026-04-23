from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.sql import func

from app.db.base import Base
from app.reminders.enums import ActorRole, ReminderState


class ReminderOccurrence(Base):
    __tablename__ = "reminder_occurrences"

    id = Column(String, primary_key=True, index=True)
    template_id = Column(String, ForeignKey("reminder_templates.id"), nullable=False, index=True)
    patient_id = Column(String, nullable=False, index=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    miss_deadline_at = Column(DateTime(timezone=True), nullable=False, index=True)

    state = Column(Enum(ReminderState), nullable=False, default=ReminderState.UPCOMING)
    state_changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    snooze_until = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    missed_at = Column(DateTime(timezone=True), nullable=True)

    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)

    completion_actor_role = Column(Enum(ActorRole), nullable=True)
    override_marked_taken = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)