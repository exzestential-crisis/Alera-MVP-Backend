from app.alerts.rules.threshold_rules import RULES


SEVERITY_RANK = {
    "warning": 1,
    "critical": 2,
}


def compare_value(value: float, operator: str, threshold: float) -> bool:
    if operator == ">":
        return value > threshold
    if operator == "<":
        return value < threshold
    if operator == ">=":
        return value >= threshold
    if operator == "<=":
        return value <= threshold
    if operator == "==":
        return value == threshold
    raise ValueError(f"Unsupported operator: {operator}")


def evaluate_thresholds(event, validation_status: str) -> dict:
    if validation_status != "valid_realtime":
        return {
            "thresholdViolated": False,
            "candidateConditions": [],
            "highestSeverity": None,
            "reason": "event not eligible for realtime threshold evaluation",
        }

    metric_type = event.metric.type
    metric_value = event.metric.value

    rules = RULES.get(metric_type, [])
    matched_conditions = []

    for rule in rules:
        if rule.get("realtime_only", False) and validation_status != "valid_realtime":
            continue

        if compare_value(metric_value, rule["operator"], rule["threshold"]):
            matched_conditions.append(rule)

    if not matched_conditions:
        return {
            "thresholdViolated": False,
            "candidateConditions": [],
            "highestSeverity": None,
            "reason": "no threshold violation",
        }

    highest = max(matched_conditions, key=lambda rule: SEVERITY_RANK[rule["severity"]])

    return {
        "thresholdViolated": True,
        "candidateConditions": [rule["condition_key"] for rule in matched_conditions],
        "highestSeverity": highest["severity"],
        "reason": None,
    }