from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder
from app.alerts.models.event_audit_log import EventAuditLog


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def create_event_audit_log(
    db,
    event_id: str,
    patient_id: str,
    logged_at: datetime,
    validation: dict,
    threshold_result: dict,
    persistence_results: list[dict],
    state: str | None,
    state_transition: dict | None,
    occurrence_created: bool,
    occurrence_conditions: list[str],
):
    logged_at = to_utc(logged_at)

    # Convert nested datetimes and other non-JSON-native values
    persistence_results_json = jsonable_encoder(persistence_results)
    candidate_conditions_json = jsonable_encoder(threshold_result["candidateConditions"])
    occurrence_conditions_json = jsonable_encoder(occurrence_conditions)

    audit_row = EventAuditLog(
        event_id=event_id,
        patient_id=patient_id,
        logged_at=logged_at,

        validation_status=validation["validation_status"],
        validation_reason=validation.get("reason"),

        threshold_violated=threshold_result["thresholdViolated"],
        candidate_conditions=candidate_conditions_json,
        highest_severity=threshold_result["highestSeverity"],
        threshold_reason=threshold_result["reason"],

        persistence_confirmed=any(
            result["persistenceConfirmed"] for result in persistence_results
        ),
        persistence_results=persistence_results_json,

        state=state,
        state_transition_from=state_transition["from"] if state_transition else None,
        state_transition_to=state_transition["to"] if state_transition else None,

        occurrence_created=occurrence_created,
        occurrence_conditions=occurrence_conditions_json,
    )

    db.add(audit_row)
    return audit_row    