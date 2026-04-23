from datetime import datetime, timezone
from typing import Any


SUPPORTED_METRICS = {"heart_rate", "spo2"}


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def validate_event_business_rules(event: Any) -> dict:
    recorded_at = to_utc(event.timestamp.recordedAt)
    received_at = to_utc(event.timestamp.receivedAt)

    if recorded_at > received_at:
        return {
            "is_valid": False,
            "validation_status": "invalid",
            "reason": "recordedAt is later than receivedAt",
            "delay_seconds": None,
        }

    delay_seconds = (received_at - recorded_at).total_seconds()

    metric_type = event.metric.type
    metric_value = event.metric.value

    if metric_type not in SUPPORTED_METRICS:
        return {
            "is_valid": False,
            "validation_status": "invalid",
            "reason": f"unsupported metric type: {metric_type}",
            "delay_seconds": delay_seconds,
        }

    if metric_type == "heart_rate":
        if not (30 <= metric_value <= 220):
            return {
                "is_valid": False,
                "validation_status": "invalid",
                "reason": "heart_rate out of valid range (30-220)",
                "delay_seconds": delay_seconds,
            }

    if metric_type == "spo2":
        if not (70 <= metric_value <= 100):
            return {
                "is_valid": False,
                "validation_status": "invalid",
                "reason": "spo2 out of valid range (70-100)",
                "delay_seconds": delay_seconds,
            }

    if delay_seconds <= 5:
        return {
            "is_valid": True,
            "validation_status": "valid_realtime",
            "reason": None,
            "delay_seconds": delay_seconds,
        }

    if delay_seconds <= 15:
        return {
            "is_valid": True,
            "validation_status": "delayed_usable",
            "reason": "event delayed beyond realtime window",
            "delay_seconds": delay_seconds,
        }

    return {
        "is_valid": False,
        "validation_status": "invalid",
        "reason": "event delayed beyond 15 seconds",
        "delay_seconds": delay_seconds,
    }