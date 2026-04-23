from datetime import datetime, timezone
from app.alerts.models.patient_state import PatientState
from app.reminders.enums import ReminderState


STATE_PRIORITY = {
    "STABLE": 0,
    "ELEVATED": 1,
    "WARNING": 2,
    "CRITICAL": 3,
}


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def determine_state(threshold_result: dict, persistence_results: list[dict]) -> str:
    # CRITICAL priority
    for result in persistence_results:
        if result["persistenceConfirmed"] and "CRITICAL" in result["conditionKey"]:
            return "CRITICAL"

    # WARNING priority
    for result in persistence_results:
        if result["persistenceConfirmed"] and "WARNING" in result["conditionKey"]:
            return "WARNING"

    # Threshold but not confirmed
    if threshold_result["thresholdViolated"]:
        return "ELEVATED"

    # Default baseline
    return "STABLE"


def update_patient_state(db, patient_id: str, new_state: str, event_time: datetime):
    event_time = to_utc(event_time)

    state_row = (
        db.query(PatientState)
        .filter(PatientState.patient_id == patient_id)
        .first()
    )

    # First time → initialize from STABLE
    if state_row is None:
        baseline_state = "STABLE"

        state_row = PatientState(
            patient_id=patient_id,
            current_state=new_state,
            last_updated_at=event_time,
        )
        db.add(state_row)

        return {
            "from": baseline_state,
            "to": new_state
        }

    old_state = state_row.current_state

    # No transition
    if old_state == new_state:
        return None

    # Apply transition
    state_row.current_state = new_state
    state_row.last_updated_at = event_time

    return {
        "from": old_state,
        "to": new_state
    }


class ReminderFSMService:
    @staticmethod
    def can_snooze(state: ReminderState) -> bool:
        return state in {ReminderState.DUE, ReminderState.SNOOZED}

    @staticmethod
    def can_mark_taken(state: ReminderState) -> bool:
        return state in {
            ReminderState.DUE,
            ReminderState.SNOOZED,
            ReminderState.MISSED,
        }

    @staticmethod
    def can_reschedule(state: ReminderState) -> bool:
        return state in {
            ReminderState.UPCOMING,
            ReminderState.DUE,
            ReminderState.SNOOZED,
            ReminderState.MISSED,
        }

    @staticmethod
    def is_terminal(state: ReminderState) -> bool:
        return state == ReminderState.COMPLETED