from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.sql import func

from app.db.base import Base
from app.reminders.enums import ActorRole
from app.db.base import Base


class ReminderNote(Base):
    __tablename__ = "reminder_notes"

    id = Column(String, primary_key=True, index=True)
    occurrence_id = Column(String, ForeignKey("reminder_occurrences.id"), nullable=False, index=True)

    author_role = Column(Enum(ActorRole), nullable=False)
    author_id = Column(String, nullable=True)

    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)