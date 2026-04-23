from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.reminders.enums import ActorRole


class ReminderNoteResponse(BaseModel):
    id: str
    occurrence_id: str
    author_role: ActorRole
    author_id: Optional[str] = None
    note_text: str
    created_at: datetime

    model_config = {"from_attributes": True}