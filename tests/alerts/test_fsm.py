from app.alerts.services.fsm_service import determine_state


def test_no_threshold_violation_returns_stable_or_normal():
    threshold_result = {
        "thresholdViolated": False,
        "candidateConditions": [],
        "highestSeverity": None,
        "reason": "no threshold violation",
    }
    persistence_results = []

    state = determine_state(threshold_result, persistence_results)

    assert state in {"STABLE", "NORMAL"}


def test_unconfirmed_threshold_violation_returns_elevated():
    threshold_result = {
        "thresholdViolated": True,
        "candidateConditions": ["HR_HIGH_WARNING"],
        "highestSeverity": "warning",
        "reason": None,
    }
    persistence_results = [
        {
            "persistenceConfirmed": False,
            "conditionKey": "HR_HIGH_WARNING",
        }
    ]

    state = determine_state(threshold_result, persistence_results)
    assert state == "ELEVATED"


def test_confirmed_warning_returns_warning():
    threshold_result = {
        "thresholdViolated": True,
        "candidateConditions": ["HR_HIGH_WARNING"],
        "highestSeverity": "warning",
        "reason": None,
    }
    persistence_results = [
        {
            "persistenceConfirmed": True,
            "conditionKey": "HR_HIGH_WARNING",
        }
    ]

    state = determine_state(threshold_result, persistence_results)
    assert state == "WARNING"


def test_confirmed_critical_overrides_warning():
    threshold_result = {
        "thresholdViolated": True,
        "candidateConditions": ["SPO2_LOW_WARNING", "SPO2_LOW_CRITICAL"],
        "highestSeverity": "critical",
        "reason": None,
    }
    persistence_results = [
        {
            "persistenceConfirmed": True,
            "conditionKey": "SPO2_LOW_WARNING",
        },
        {
            "persistenceConfirmed": True,
            "conditionKey": "SPO2_LOW_CRITICAL",
        }
    ]

    state = determine_state(threshold_result, persistence_results)
    assert state == "CRITICAL"