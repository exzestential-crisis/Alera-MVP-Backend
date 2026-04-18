RULES = {
    "heart_rate": [
        {
            "condition_key": "HR_HIGH_WARNING",
            "label": "High heart rate warning",
            "operator": ">",
            "threshold": 110,
            "severity": "warning",
            "realtime_only": True,
        },
        {
            "condition_key": "HR_HIGH_CRITICAL",
            "label": "High heart rate critical",
            "operator": ">",
            "threshold": 130,
            "severity": "critical",
            "realtime_only": True,
        },
    ],
    "spo2": [
        {
            "condition_key": "SPO2_LOW_WARNING",
            "label": "Low oxygen warning",
            "operator": "<",
            "threshold": 92,
            "severity": "warning",
            "realtime_only": True,
        },
        {
            "condition_key": "SPO2_LOW_CRITICAL",
            "label": "Low oxygen critical",
            "operator": "<",
            "threshold": 90,
            "severity": "critical",
            "realtime_only": True,
        },
    ],
}