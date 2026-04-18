from datetime import datetime, timezone
from app.models.patient_monitoring_status import PatientMonitoringStatus


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def update_last_valid_realtime_event(db, patient_id: str, event_time: datetime):
    event_time = to_utc(event_time)

    row = (
        db.query(PatientMonitoringStatus)
        .filter(PatientMonitoringStatus.patient_id == patient_id)
        .first()
    )

    if row is None:
        row = PatientMonitoringStatus(
            patient_id=patient_id,
            last_valid_realtime_event_at=event_time,
        )
        db.add(row)
        return row

    row.last_valid_realtime_event_at = event_time
    return row