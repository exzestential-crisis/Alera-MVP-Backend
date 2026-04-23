from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.reminders.enums import ActorRole


class SnoozeRequest(BaseModel):
    actor_id: str
    actor_role: ActorRole
    minutes: int = Field(ge=1, le=60)


class MarkTakenRequest(BaseModel):
    actor_id: str
    actor_role: ActorRole
    note: Optional[str] = None


class RescheduleRequest(BaseModel):
    actor_id: str
    actor_role: ActorRole
    new_scheduled_at: datetime
    reason: Optional[str] = None


class ResolveMissedRequest(BaseModel):
    actor_id: str
    actor_role: ActorRole
    note: Optional[str] = None


class AddNoteRequest(BaseModel):
    actor_id: str
    actor_role: ActorRole
    text: str = Field(min_length=1)