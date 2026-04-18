from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from datetime import datetime, timezone

from app.db import engine, SessionLocal, Base, DATABASE_URL
from app.core.rules import RULES

from app.models.raw_event import RawEvent
from app.models.patient_monitoring_status import PatientMonitoringStatus
from app.models.condition_tracker import ConditionTracker
from app.models.patient_state import PatientState
from app.models.occurrence import Occurrence
from app.models.event_audit_log import EventAuditLog

from app.schemas.event_schema import Event

from app.services.validation_service import validate_event_business_rules
from app.services.monitoring_status_service import update_last_valid_realtime_event
from app.services.system_condition_service import check_no_data_condition
from app.services.threshold_service import evaluate_thresholds
from app.services.persistence_service import (
    update_and_check_persistence,
    reset_missing_trackers_for_metric,
)
from app.services.fsm_service import determine_state, update_patient_state
from app.services.occurrence_service import create_occurrence
from app.services.audit_log_service import create_event_audit_log

app = FastAPI(title="Alera DSS Backend")

Base.metadata.create_all(bind=engine)


@app.get("/rules")
def list_rules():
    return RULES


@app.get("/debug/db-info")
def debug_db_info():
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT current_database(), current_user, current_schema()")
        ).fetchone()

    return {
        "database_url": DATABASE_URL,
        "current_database": row[0],
        "current_user": row[1],
        "current_schema": row[2],
    }


@app.get("/debug/db-counts")
def debug_db_counts():
    db = SessionLocal()
    try:
        return {
            "raw_events": db.query(RawEvent).count(),
            "condition_trackers": db.query(ConditionTracker).count(),
            "patient_states": db.query(PatientState).count(),
            "occurrences": db.query(Occurrence).count(),
        }
    finally:
        db.close()


@app.get("/patients/{patient_id}/check-no-data")
def check_patient_no_data(patient_id: str):
    db = SessionLocal()
    try:
        result = check_no_data_condition(
            db=db,
            patient_id=patient_id,
            now=datetime.now(timezone.utc)
        )
        return result
    finally:
        db.close()
        

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/events")
def list_events():
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@app.get("/patient-states")
def list_patient_states():
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@app.get("/condition-trackers")
def list_condition_trackers():
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@app.get("/occurrences")
def list_occurrences():
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@app.get("/audit-logs")
def list_audit_logs():
    db = SessionLocal()
    try:
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
                } if row.state_transition_from is not None or row.state_transition_to is not None else None,
                "occurrenceCreated": row.occurrence_created,
                "occurrenceConditions": row.occurrence_conditions,
            }
            for row in rows
        ]
    finally:
        db.close()


@app.get("/audit-logs/{event_id}")
def get_audit_log(event_id: str):
    db = SessionLocal()
    try:
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
            } if row.state_transition_from is not None or row.state_transition_to is not None else None,
            "occurrenceCreated": row.occurrence_created,
            "occurrenceConditions": row.occurrence_conditions,
        }
    finally:
        db.close()
        

@app.post("/events")
def ingest_event(event: Event):
    """
    Main event-ingestion pipeline for Alera.

    Processing order:
    1. Validate event business rules
    2. Evaluate threshold violations
    3. Reset missing trackers for the current metric only
    4. Update persistence for currently matched conditions
    5. Determine FSM state
    6. Update patient state row
    7. Create occurrence(s) only for newly confirmed conditions
    8. Store raw event
    9. Commit everything as one transaction
    """
    db = SessionLocal()
    try:
        # ------------------------------------------------------------
        # 1. Business validation
        # ------------------------------------------------------------
        # Determines whether the event is:
        # - valid_realtime
        # - delayed_usable
        # - invalid
        validation = validate_event_business_rules(event)

        system_conditions = []

        if validation["validation_status"] == "delayed_usable":
            system_conditions.append("DELAYED_DATA")

        if validation["validation_status"] == "invalid":
            system_conditions.append("INVALID_EVENT")

        if validation["validation_status"] == "valid_realtime":
            update_last_valid_realtime_event(
                db=db,
                patient_id=event.patientId,
                event_time=event.timestamp.recordedAt
            )

        # ------------------------------------------------------------
        # 2. Threshold evaluation
        # ------------------------------------------------------------
        # Only valid_realtime events should actually produce realtime
        # candidate conditions. Delayed/invalid events should not.
        threshold_result = evaluate_thresholds(
            event=event,
            validation_status=validation["validation_status"]
        )

        # Current candidate conditions detected from THIS event only.
        # If threshold is not violated, this becomes an empty list.
        current_conditions = (
            threshold_result["candidateConditions"]
            if threshold_result["thresholdViolated"]
            else []
        )

        # ------------------------------------------------------------
        # 3. Reset trackers that disappeared for THIS METRIC only
        # ------------------------------------------------------------
        # Important:
        # - Only realtime-valid events may affect persistence/reset logic
        # - Only trackers for the current metric may be reset
        # This prevents:
        # - delayed/invalid data from resetting trackers
        # - HR events from resetting SpO₂ trackers
        if validation["validation_status"] == "valid_realtime":
            reset_missing_trackers_for_metric(
                db=db,
                patient_id=event.patientId,
                metric_type=event.metric.type,
                current_candidate_conditions=current_conditions
            )

        # ------------------------------------------------------------
        # 4. Persistence update
        # ------------------------------------------------------------
        # For each currently matched candidate condition:
        # - start tracker if first abnormal event
        # - continue tracker if already active
        # - confirm once elapsed time reaches required duration
        persistence_results = []

        if (
            validation["validation_status"] == "valid_realtime"
            and threshold_result["thresholdViolated"]
        ):
            for condition_key in threshold_result["candidateConditions"]:
                persistence_result = update_and_check_persistence(
                    db=db,
                    patient_id=event.patientId,
                    condition_key=condition_key,
                    event_time=event.timestamp.recordedAt,
                )
                persistence_results.append(persistence_result)

        # ------------------------------------------------------------
        # 5. FSM state determination
        # ------------------------------------------------------------
        # FSM must happen AFTER persistence results are known.
        # State rules:
        # - CRITICAL if any confirmed critical condition
        # - WARNING if any confirmed warning condition
        # - ELEVATED if threshold violated but not yet confirmed
        # - NORMAL otherwise

        # ------------------------------------------------------------
        # 6. Persist / update patient state row
        # ------------------------------------------------------------
        # This returns:
        # - None if state did not change
        # - {"from": old_state, "to": new_state} if it did

        if validation["validation_status"] == "valid_realtime":
            new_state = determine_state(
                threshold_result=threshold_result,
                persistence_results=persistence_results
            )

            state_transition = update_patient_state(
                db=db,
                patient_id=event.patientId,
                new_state=new_state,
                event_time=event.timestamp.recordedAt
            )
        else:
            new_state = None
            state_transition = None

        # ------------------------------------------------------------
        # 7. Occurrence creation
        # ------------------------------------------------------------
        # Create occurrence(s) ONLY when a condition is newly confirmed.
        # Do NOT create an occurrence every time persistenceConfirmed=True,
        # because that would duplicate occurrences on later events.
        occurrence_rows = []
        occurrence_created = False

        for result in persistence_results:
            if result.get("justConfirmed", False):
                occurrence = create_occurrence(
                    db=db,
                    patient_id=event.patientId,
                    condition_key=result["conditionKey"],
                    state_at_creation=new_state,
                    source_event_id=event.eventId,
                    created_at=event.timestamp.recordedAt,
                )
                occurrence_rows.append(occurrence)
                occurrence_created = True

        # ------------------------------------------------------------
        # 8. Store raw inbound event
        # ------------------------------------------------------------
        # Raw event storage preserves:
        # - original payload traceability
        # - validation metadata
        # - audit/debug capability
        raw_event = RawEvent(
            event_id=event.eventId,
            patient_id=event.patientId,
            metric_type=event.metric.type,
            metric_value=event.metric.value,
            metric_unit=event.metric.unit,
            recorded_at=event.timestamp.recordedAt,
            received_at=event.timestamp.receivedAt,
            device_id=event.device.id if event.device else None,
            device_type=event.device.type if event.device else None,
            battery_level=event.device.batteryLevel if event.device else None,
            is_connected=event.device.isConnected if event.device else None,
            validation_status=validation["validation_status"],
            validation_reason=validation.get("reason"),
            delay_seconds=validation.get("delay_seconds"),
            raw_json=event.model_dump(mode="json"),
        )

        occurrence_conditions = [o.condition_key for o in occurrence_rows]

        create_event_audit_log(
            db=db,
            event_id=event.eventId,
            patient_id=event.patientId,
            logged_at=event.timestamp.recordedAt,
            validation=validation,
            threshold_result=threshold_result,
            persistence_results=persistence_results,
            state=new_state,
            state_transition=state_transition,
            occurrence_created=occurrence_created,
            occurrence_conditions=occurrence_conditions,
        )

        db.add(raw_event)

        # ------------------------------------------------------------
        # 9. Commit everything once
        # ------------------------------------------------------------
        # This keeps the event pipeline atomic:
        # either all changes persist together, or none do.
        db.commit()
        db.refresh(raw_event)

        # ------------------------------------------------------------
        # 10. Structured API response
        # ------------------------------------------------------------
        return {
            "accepted": validation["is_valid"],
            "stored": True,
            "eventId": raw_event.event_id,
            "validationStatus": raw_event.validation_status,
            "validationReason": raw_event.validation_reason,
            "delaySeconds": raw_event.delay_seconds,
            "thresholdViolated": threshold_result["thresholdViolated"],
            "candidateConditions": threshold_result["candidateConditions"],
            "highestSeverity": threshold_result["highestSeverity"],
            "thresholdReason": threshold_result["reason"],
            "persistenceResults": persistence_results,
            "persistenceConfirmed": any(
                result["persistenceConfirmed"] for result in persistence_results
            ),
            "state": new_state,
            "stateTransition": state_transition,
            "occurrenceCreated": occurrence_created,
            "occurrenceCount": len(occurrence_rows),
            "occurrenceConditions": occurrence_conditions,
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate eventId.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()