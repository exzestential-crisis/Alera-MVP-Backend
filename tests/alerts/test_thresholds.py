from types import SimpleNamespace
from datetime import datetime, timezone

from app.alerts.services.threshold_service import evaluate_thresholds


def make_event(metric_type, value):
    now = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        metric=SimpleNamespace(
            type=metric_type,
            value=value,
            unit="bpm" if metric_type == "heart_rate" else "%"
        ),
        timestamp=SimpleNamespace(
            recordedAt=now,
            receivedAt=now
        )
    )


def test_hr_110_does_not_trigger_warning():
    event = make_event("heart_rate", 110)
    result = evaluate_thresholds(event, "valid_realtime")

    assert result["thresholdViolated"] is False
    assert result["candidateConditions"] == []


def test_hr_111_triggers_warning():
    event = make_event("heart_rate", 111)
    result = evaluate_thresholds(event, "valid_realtime")

    assert result["thresholdViolated"] is True
    assert "HR_HIGH_WARNING" in result["candidateConditions"]
    assert result["highestSeverity"] == "warning"


def test_hr_131_triggers_warning_and_critical():
    event = make_event("heart_rate", 131)
    result = evaluate_thresholds(event, "valid_realtime")

    assert result["thresholdViolated"] is True
    assert "HR_HIGH_WARNING" in result["candidateConditions"]
    assert "HR_HIGH_CRITICAL" in result["candidateConditions"]
    assert result["highestSeverity"] == "critical"


def test_spo2_92_does_not_trigger_warning():
    event = make_event("spo2", 92)
    result = evaluate_thresholds(event, "valid_realtime")

    assert result["thresholdViolated"] is False
    assert result["candidateConditions"] == []


def test_spo2_91_triggers_warning():
    event = make_event("spo2", 91)
    result = evaluate_thresholds(event, "valid_realtime")

    assert result["thresholdViolated"] is True
    assert "SPO2_LOW_WARNING" in result["candidateConditions"]
    assert result["highestSeverity"] == "warning"


def test_spo2_89_triggers_warning_and_critical():
    event = make_event("spo2", 89)
    result = evaluate_thresholds(event, "valid_realtime")

    assert result["thresholdViolated"] is True
    assert "SPO2_LOW_WARNING" in result["candidateConditions"]
    assert "SPO2_LOW_CRITICAL" in result["candidateConditions"]
    assert result["highestSeverity"] == "critical"


def test_delayed_event_does_not_run_threshold_logic():
    event = make_event("heart_rate", 140)
    result = evaluate_thresholds(event, "delayed_usable")

    assert result["thresholdViolated"] is False
    assert result["candidateConditions"] == []
    assert result["highestSeverity"] is None