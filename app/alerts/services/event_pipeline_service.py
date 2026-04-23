from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from app.alerts.schemas.event_schema import Event

from app.alerts.models.raw_event import RawEvent

from app.alerts.services.validation_service import validate_event_business_rules
from app.alerts.services.monitoring_status_service import update_last_valid_realtime_event
from app.alerts.services.threshold_service import evaluate_thresholds
from app.alerts.services.persistence_service import (
    update_and_check_persistence,
    reset_missing_trackers_for_metric,
)
from app.alerts.services.fsm_service import determine_state, update_patient_state
from app.alerts.services.occurrence_service import create_occurrence
from app.alerts.services.audit_log_service import create_event_audit_log


def process_incoming_event(db: Session, event: Event):
    try:
        # -----------------------------
        # 1. Validation
        # -----------------------------
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

        # -----------------------------
        # 2. Threshold evaluation
        # -----------------------------
        threshold_result = evaluate_thresholds(
            event=event,
            validation_status=validation["validation_status"]
        )

        current_conditions = (
            threshold_result["candidateConditions"]
            if threshold_result["thresholdViolated"]
            else []
        )

        # -----------------------------
        # 3. Reset trackers
        # -----------------------------
        if validation["validation_status"] == "valid_realtime":
            reset_missing_trackers_for_metric(
                db=db,
                patient_id=event.patientId,
                metric_type=event.metric.type,
                current_candidate_conditions=current_conditions
            )

        # -----------------------------
        # 4. Persistence
        # -----------------------------
        persistence_results = []

        if (
            validation["validation_status"] == "valid_realtime"
            and threshold_result["thresholdViolated"]
        ):
            for condition_key in threshold_result["candidateConditions"]:
                result = update_and_check_persistence(
                    db=db,
                    patient_id=event.patientId,
                    condition_key=condition_key,
                    event_time=event.timestamp.recordedAt,
                )
                persistence_results.append(result)

        # -----------------------------
        # 5. FSM
        # -----------------------------
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

        # -----------------------------
        # 6. Occurrences
        # -----------------------------
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

        # -----------------------------
        # 7. Raw event
        # -----------------------------
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
        db.commit()
        db.refresh(raw_event)

        # -----------------------------
        # 8. Response
        # -----------------------------
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
                r["persistenceConfirmed"] for r in persistence_results
            ),
            "state": new_state,
            "stateTransition": state_transition,
            "occurrenceCreated": occurrence_created,
            "occurrenceCount": len(occurrence_rows),
            "occurrenceConditions": occurrence_conditions,
        }

    except IntegrityError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise