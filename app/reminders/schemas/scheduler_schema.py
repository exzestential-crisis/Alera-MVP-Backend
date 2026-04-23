from pydantic import BaseModel


class SchedulerRunResponse(BaseModel):
    ran_at: str
    upcoming_to_due: int
    snoozed_to_due: int
    due_to_missed: int
    snoozed_to_missed: int
    total_changed: int