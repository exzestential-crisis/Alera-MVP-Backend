from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.reminders.enums import ReminderState

class ManualOccurrenceCreate(BaseModel):
    template_id: str
    patient_id: str
    scheduled_at: datetime

class ReminderOccurrenceResponse(BaseModel):
    id: str
    template_id: str
    patient_id: str
    scheduled_at: datetime
    due_at: datetime
    miss_deadline_at: datetime
    state: ReminderState
    state_changed_at: datetime
    snooze_until: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    missed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    override_marked_taken: bool

    model_config = {"from_attributes": True}