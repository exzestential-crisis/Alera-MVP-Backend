from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

from app.services.validation_service import validate_event_business_rules


def make_event(metric_type, value, recorded_at, received_at):
    return SimpleNamespace(
        metric=SimpleNamespace(
            type=metric_type,
            value=value,
            unit="bpm" if metric_type == "heart_rate" else "%"
        ),
        timestamp=SimpleNamespace(
            recordedAt=recorded_at,
            receivedAt=received_at
        )
    )


def test_valid_realtime_heart_rate():
    recorded = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
    received = recorded + timedelta(seconds=3)

    event = make_event("heart_rate", 85, recorded, received)
    result = validate_event_business_rules(event)

    assert result["is_valid"] is True
    assert result["validation_status"] == "valid_realtime"


def test_delayed_usable_event():
    recorded = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
    received = recorded + timedelta(seconds=10)

    event = make_event("heart_rate", 140, recorded, received)
    result = validate_event_business_rules(event)

    assert result["is_valid"] is True
    assert result["validation_status"] == "delayed_usable"


def test_invalid_stale_event():
    recorded = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
    received = recorded + timedelta(seconds=20)

    event = make_event("heart_rate", 140, recorded, received)
    result = validate_event_business_rules(event)

    assert result["is_valid"] is False
    assert result["validation_status"] == "invalid"


def test_invalid_heart_rate_range():
    recorded = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
    received = recorded + timedelta(seconds=3)

    event = make_event("heart_rate", 500, recorded, received)
    result = validate_event_business_rules(event)

    assert result["is_valid"] is False
    assert result["validation_status"] == "invalid"


def test_invalid_spo2_range():
    recorded = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
    received = recorded + timedelta(seconds=3)

    event = make_event("spo2", 40, recorded, received)
    result = validate_event_business_rules(event)

    assert result["is_valid"] is False
    assert result["validation_status"] == "invalid"


def test_invalid_timestamp_order():
    recorded = datetime(2026, 4, 20, 10, 0, 5, tzinfo=timezone.utc)
    received = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)

    event = make_event("heart_rate", 90, recorded, received)
    result = validate_event_business_rules(event)

    assert result["is_valid"] is False
    assert result["validation_status"] == "invalid"