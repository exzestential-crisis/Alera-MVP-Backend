from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.reminders.enums import ActorRole, ReminderActionType, ReminderState


class ReminderActionLogResponse(BaseModel):
    id: str
    occurrence_id: str
    actor_role: ActorRole
    actor_id: Optional[str] = None
    action_type: ReminderActionType
    from_state: Optional[ReminderState] = None
    to_state: Optional[ReminderState] = None
    metadata_json: Optional[str] = None
    action_at: datetime

    model_config = {"from_attributes": True}