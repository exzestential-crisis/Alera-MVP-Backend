from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.reminders.enums import RecurrenceType, ReminderCategory


class ReminderTemplateCreate(BaseModel):
    patient_id: str
    created_by: str
    category: ReminderCategory
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    recurrence_type: RecurrenceType
    recurrence_rule: Optional[str] = None
    default_time: str  # validate stricter later
    timezone: str = "UTC"
    start_date: date
    end_date: Optional[date] = None


class ReminderTemplateResponse(BaseModel):
    id: str
    patient_id: str
    created_by: str
    category: ReminderCategory
    title: str
    description: Optional[str]
    recurrence_type: RecurrenceType
    recurrence_rule: Optional[str]
    default_time: str
    timezone: str
    start_date: date
    end_date: Optional[date]
    is_active: bool

    model_config = {"from_attributes": True}