from datetime import datetime, timezone
from app.alerts.models.condition_tracker import ConditionTracker
from app.alerts.rules.persistence_rules import PERSISTENCE_RULES


METRIC_CONDITION_KEYS = {
    "heart_rate": {
        "HR_HIGH_WARNING",
        "HR_HIGH_CRITICAL",
    },
    "spo2": {
        "SPO2_LOW_WARNING",
        "SPO2_LOW_CRITICAL",
    },
}


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_required_duration(condition_key: str) -> int:
    return PERSISTENCE_RULES.get(condition_key, 0)


def update_and_check_persistence(
    db,
    patient_id: str,
    condition_key: str,
    event_time: datetime,
) -> dict:
    event_time = to_utc(event_time)

    tracker = (
        db.query(ConditionTracker)
        .filter(
            ConditionTracker.patient_id == patient_id,
            ConditionTracker.condition_key == condition_key,
            ConditionTracker.active.is_(True),
        )
        .first()
    )

    required_duration = get_required_duration(condition_key)

    # ------------------------------------------------------------
    # Immediate confirmation rules (duration = 0)
    # ------------------------------------------------------------
    if required_duration == 0:
        if tracker is None:
            tracker = ConditionTracker(
                patient_id=patient_id,
                condition_key=condition_key,
                active=True,
                started_at=event_time,
                last_seen_at=event_time,
                duration_seconds=0.0,
                confirmed=True,
            )
            db.add(tracker)

            just_confirmed = True  # first time we see this condition

        else:
            was_confirmed = tracker.confirmed

            tracker.last_seen_at = event_time
            tracker.confirmed = True

            just_confirmed = not was_confirmed

        return {
            "persistenceConfirmed": True,
            "justConfirmed": just_confirmed,
            "conditionKey": condition_key,
            "requiredDuration": required_duration,
            "elapsedSeconds": tracker.duration_seconds,
            "startedAt": tracker.started_at,
            "lastSeenAt": tracker.last_seen_at,
        }

    # ------------------------------------------------------------
    # First abnormal event → start tracker
    # ------------------------------------------------------------
    if tracker is None:
        tracker = ConditionTracker(
            patient_id=patient_id,
            condition_key=condition_key,
            active=True,
            started_at=event_time,
            last_seen_at=event_time,
            duration_seconds=0.0,
            confirmed=False,
        )
        db.add(tracker)

        return {
            "persistenceConfirmed": False,
            "justConfirmed": False,
            "conditionKey": condition_key,
            "requiredDuration": required_duration,
            "elapsedSeconds": 0.0,
            "startedAt": tracker.started_at,
            "lastSeenAt": tracker.last_seen_at,
        }

    # ------------------------------------------------------------
    # Continue timer
    # ------------------------------------------------------------
    was_confirmed = tracker.confirmed

    tracker.last_seen_at = event_time

    elapsed_seconds = (
        to_utc(tracker.last_seen_at) - to_utc(tracker.started_at)
    ).total_seconds()

    tracker.duration_seconds = elapsed_seconds

    if elapsed_seconds >= required_duration:
        tracker.confirmed = True

    just_confirmed = (not was_confirmed) and tracker.confirmed

    return {
        "persistenceConfirmed": tracker.confirmed,
        "justConfirmed": just_confirmed,
        "conditionKey": condition_key,
        "requiredDuration": required_duration,
        "elapsedSeconds": tracker.duration_seconds,
        "startedAt": tracker.started_at,
        "lastSeenAt": tracker.last_seen_at,
    }


def reset_condition_tracker(db, patient_id: str, condition_key: str) -> None:
    tracker = (
        db.query(ConditionTracker)
        .filter(
            ConditionTracker.patient_id == patient_id,
            ConditionTracker.condition_key == condition_key,
            ConditionTracker.active.is_(True),
        )
        .first()
    )

    if tracker:
        tracker.active = False


def reset_missing_trackers_for_metric(
    db,
    patient_id: str,
    metric_type: str,
    current_candidate_conditions: list[str],
) -> None:
    relevant_keys = METRIC_CONDITION_KEYS.get(metric_type, set())

    if not relevant_keys:
        return

    active_trackers = (
        db.query(ConditionTracker)
        .filter(
            ConditionTracker.patient_id == patient_id,
            ConditionTracker.active.is_(True),
            ConditionTracker.condition_key.in_(relevant_keys),
        )
        .all()
    )

    for tracker in active_trackers:
        if tracker.condition_key not in current_candidate_conditions:
            tracker.active = False