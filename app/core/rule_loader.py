from app.core.rules import RULES


def get_metric_rules(metric_type: str) -> dict | None:
    return RULES.get(metric_type)