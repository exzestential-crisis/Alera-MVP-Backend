from datetime import datetime, timezone
from app.alerts.models.patient_monitoring_status import PatientMonitoringStatus


NO_DATA_THRESHOLD_SECONDS = 60


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_no_data_condition(db, patient_id: str, now: datetime) -> dict:
    now = to_utc(now)

    row = (
        db.query(PatientMonitoringStatus)
        .filter(PatientMonitoringStatus.patient_id == patient_id)
        .first()
    )

    if row is None or row.last_valid_realtime_event_at is None:
        return {
            "patientId": patient_id,
            "systemConditions": ["NO_DATA"],
            "systemAlertCreated": True,
            "reason": "no valid realtime event has ever been recorded"
        }

    elapsed = (now - to_utc(row.last_valid_realtime_event_at)).total_seconds()

    if elapsed >= NO_DATA_THRESHOLD_SECONDS:
        return {
            "patientId": patient_id,
            "systemConditions": ["NO_DATA"],
            "systemAlertCreated": True,
            "elapsedSecondsSinceLastValidRealtimeEvent": elapsed,
            "reason": "no valid realtime data for >= 60 seconds"
        }

    return {
        "patientId": patient_id,
        "systemConditions": [],
        "systemAlertCreated": False,
        "elapsedSecondsSinceLastValidRealtimeEvent": elapsed,
        "reason": "realtime data still within allowed window"
    }