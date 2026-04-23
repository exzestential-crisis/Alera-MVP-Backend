from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import get_db
from app.alerts.rules.threshold_rules import RULES

from app.alerts.models.raw_event import RawEvent
from app.alerts.models.condition_tracker import ConditionTracker
from app.alerts.models.patient_state import PatientState
from app.alerts.models.alert_occurrence import Occurrence
from app.alerts.models.event_audit_log import EventAuditLog

from app.alerts.schemas.event_schema import Event

from app.alerts.services.system_condition_service import check_no_data_condition
from app.alerts.services.event_pipeline_service import process_incoming_event

router = APIRouter()


@router.get("/rules")
def list_rules():
    return RULES


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/events")
def list_events(db: Session = Depends(get_db)):
    events = db.query(RawEvent).order_by(RawEvent.id.desc()).all()
    return [
        {
            "id": event.id,
            "eventId": event.event_id,
            "patientId": event.patient_id,
            "metricType": event.metric_type,
            "metricValue": event.metric_value,
            "validationStatus": event.validation_status,
            "validationReason": event.validation_reason,
            "delaySeconds": event.delay_seconds,
            "recordedAt": event.recorded_at,
            "receivedAt": event.received_at,
        }
        for event in events
    ]


@router.get("/patient-states")
def list_patient_states(db: Session = Depends(get_db)):
    states = db.query(PatientState).order_by(PatientState.id.desc()).all()
    return [
        {
            "id": s.id,
            "patientId": s.patient_id,
            "currentState": s.current_state,
            "lastUpdatedAt": s.last_updated_at,
        }
        for s in states
    ]


@router.get("/condition-trackers")
def list_condition_trackers(db: Session = Depends(get_db)):
    trackers = db.query(ConditionTracker).order_by(ConditionTracker.id.desc()).all()
    return [
        {
            "id": t.id,
            "patientId": t.patient_id,
            "conditionKey": t.condition_key,
            "active": t.active,
            "startedAt": t.started_at,
            "lastSeenAt": t.last_seen_at,
            "durationSeconds": t.duration_seconds,
            "confirmed": t.confirmed,
        }
        for t in trackers
    ]


@router.get("/occurrences")
def list_occurrences(db: Session = Depends(get_db)):
    occurrences = db.query(Occurrence).order_by(Occurrence.id.desc()).all()
    return [
        {
            "id": o.id,
            "patientId": o.patient_id,
            "conditionKey": o.condition_key,
            "severity": o.severity,
            "stateAtCreation": o.state_at_creation,
            "sourceEventId": o.source_event_id,
            "createdAt": o.created_at,
            "active": o.active,
        }
        for o in occurrences
    ]


@router.get("/audit-logs")
def list_audit_logs(db: Session = Depends(get_db)):
    rows = db.query(EventAuditLog).order_by(EventAuditLog.id.desc()).all()
    return [
        {
            "id": row.id,
            "eventId": row.event_id,
            "patientId": row.patient_id,
            "loggedAt": row.logged_at,
            "validationStatus": row.validation_status,
            "validationReason": row.validation_reason,
            "thresholdViolated": row.threshold_violated,
            "candidateConditions": row.candidate_conditions,
            "highestSeverity": row.highest_severity,
            "thresholdReason": row.threshold_reason,
            "persistenceConfirmed": row.persistence_confirmed,
            "persistenceResults": row.persistence_results,
            "state": row.state,
            "stateTransition": {
                "from": row.state_transition_from,
                "to": row.state_transition_to,
            } if row.state_transition_from or row.state_transition_to else None,
            "occurrenceCreated": row.occurrence_created,
            "occurrenceConditions": row.occurrence_conditions,
        }
        for row in rows
    ]


@router.get("/audit-logs/{event_id}")
def get_audit_log(event_id: str, db: Session = Depends(get_db)):
    row = (
        db.query(EventAuditLog)
        .filter(EventAuditLog.event_id == event_id)
        .first()
    )

    if row is None:
        raise HTTPException(status_code=404, detail="Audit log not found.")

    return {
        "id": row.id,
        "eventId": row.event_id,
        "patientId": row.patient_id,
        "loggedAt": row.logged_at,
        "validationStatus": row.validation_status,
        "validationReason": row.validation_reason,
        "thresholdViolated": row.threshold_violated,
        "candidateConditions": row.candidate_conditions,
        "highestSeverity": row.highest_severity,
        "thresholdReason": row.threshold_reason,
        "persistenceConfirmed": row.persistence_confirmed,
        "persistenceResults": row.persistence_results,
        "state": row.state,
        "stateTransition": {
            "from": row.state_transition_from,
            "to": row.state_transition_to,
        } if row.state_transition_from or row.state_transition_to else None,
        "occurrenceCreated": row.occurrence_created,
        "occurrenceConditions": row.occurrence_conditions,
    }


@router.get("/patients/{patient_id}/check-no-data")
def check_patient_no_data_endpoint(
    patient_id: str,
    db: Session = Depends(get_db)
):
    return check_no_data_condition(
        db=db,
        patient_id=patient_id,
        now=datetime.now(timezone.utc)
    )


@router.post("/events")
def ingest_event(event: Event, db: Session = Depends(get_db)):
    try:
        return process_incoming_event(db=db, event=event)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Duplicate eventId.")