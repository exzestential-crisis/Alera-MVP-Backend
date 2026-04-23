from datetime import datetime, timezone
from app.alerts.models.alert_occurrence import Occurrence


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def infer_severity_from_condition(condition_key: str) -> str:
    if "CRITICAL" in condition_key:
        return "critical"
    if "WARNING" in condition_key:
        return "warning"
    return "unknown"


def create_occurrence(
    db,
    patient_id: str,
    condition_key: str,
    state_at_creation: str,
    source_event_id: str,
    created_at: datetime,
):
    created_at = to_utc(created_at)

    occurrence = Occurrence(
        patient_id=patient_id,
        condition_key=condition_key,
        severity=infer_severity_from_condition(condition_key),
        state_at_creation=state_at_creation,
        source_event_id=source_event_id,
        created_at=created_at,
        active=True,
    )

    db.add(occurrence)

    return occurrence