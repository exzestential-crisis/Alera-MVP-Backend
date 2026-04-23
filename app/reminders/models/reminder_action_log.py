from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.sql import func

from app.db.base import Base
from app.reminders.enums import ActorRole, ReminderActionType, ReminderState


class ReminderActionLog(Base):
    __tablename__ = "reminder_action_logs"

    id = Column(String, primary_key=True, index=True)
    occurrence_id = Column(String, ForeignKey("reminder_occurrences.id"), nullable=False, index=True)

    actor_role = Column(Enum(ActorRole), nullable=False)
    actor_id = Column(String, nullable=True)

    action_type = Column(Enum(ReminderActionType), nullable=False)

    from_state = Column(Enum(ReminderState), nullable=True)
    to_state = Column(Enum(ReminderState), nullable=True)

    metadata_json = Column(Text, nullable=True)
    action_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)