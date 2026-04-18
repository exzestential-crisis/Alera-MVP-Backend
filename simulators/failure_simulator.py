import time
import uuid
import requests
from datetime import datetime, timedelta, timezone

EVENTS_URL = "http://127.0.0.1:8000/events"
NO_DATA_URL_TEMPLATE = "http://127.0.0.1:8000/patients/{patient_id}/check-no-data"


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_event(
    patient_id: str,
    metric_type: str,
    value: float,
    unit: str,
    recorded_at: datetime,
    delay_seconds: int = 3,
    device_id: str = "failure_sim_watch_01",
    event_id: str | None = None,
):
    received_at = recorded_at + timedelta(seconds=delay_seconds)

    return {
        "eventId": event_id or f"evt_{uuid.uuid4().hex[:12]}",
        "patientId": patient_id,
        "metric": {
            "type": metric_type,
            "value": value,
            "unit": unit
        },
        "timestamp": {
            "recordedAt": iso_z(recorded_at),
            "receivedAt": iso_z(received_at)
        },
        "device": {
            "id": device_id,
            "type": "smartwatch",
            "batteryLevel": 80,
            "isConnected": True
        }
    }


def post_event(event: dict):
    response = requests.post(EVENTS_URL, json=event, timeout=10)

    try:
        data = response.json()
    except Exception:
        data = {"raw_text": response.text}

    print("-" * 100)
    print(f"POST /events | patient={event['patientId']} | eventId={event['eventId']}")
    print(f"metric={event['metric']['type']} value={event['metric']['value']}{event['metric']['unit']}")
    print(f"recordedAt={event['timestamp']['recordedAt']} receivedAt={event['timestamp']['receivedAt']}")
    print(f"status_code={response.status_code}")
    print(f"response={data}")

    return response.status_code, data


def check_no_data(patient_id: str):
    url = NO_DATA_URL_TEMPLATE.format(patient_id=patient_id)
    response = requests.get(url, timeout=10)

    try:
        data = response.json()
    except Exception:
        data = {"raw_text": response.text}

    print("-" * 100)
    print(f"GET /patients/{patient_id}/check-no-data")
    print(f"status_code={response.status_code}")
    print(f"response={data}")

    return response.status_code, data


def run_scenario(name: str, fn):
    print("\n" + "=" * 100)
    print(f"RUNNING SCENARIO: {name}")
    print("=" * 100)
    fn()
    print("=" * 100)
    print(f"END SCENARIO: {name}")
    print("=" * 100 + "\n")


# ------------------------------------------------------------------
# SCENARIO 1: VALID REALTIME EVENT
# ------------------------------------------------------------------
def scenario_valid_realtime():
    start = datetime.now(timezone.utc)
    patient_id = "fail_valid_001"

    event = build_event(
        patient_id=patient_id,
        metric_type="heart_rate",
        value=85,
        unit="bpm",
        recorded_at=start,
        delay_seconds=3,
    )

    post_event(event)


# ------------------------------------------------------------------
# SCENARIO 2: DELAYED USABLE EVENT
# Expected:
# - validationStatus = delayed_usable
# - stored = true
# - no realtime threshold / persistence / occurrence behavior
# ------------------------------------------------------------------
def scenario_delayed_usable():
    start = datetime.now(timezone.utc)
    patient_id = "fail_delayed_001"

    event = build_event(
        patient_id=patient_id,
        metric_type="heart_rate",
        value=140,
        unit="bpm",
        recorded_at=start,
        delay_seconds=10,
    )

    post_event(event)


# ------------------------------------------------------------------
# SCENARIO 3: INVALID STALE EVENT
# Expected:
# - validationStatus = invalid
# - rejected from realtime logic
# ------------------------------------------------------------------
def scenario_invalid_stale():
    start = datetime.now(timezone.utc)
    patient_id = "fail_stale_001"

    event = build_event(
        patient_id=patient_id,
        metric_type="heart_rate",
        value=140,
        unit="bpm",
        recorded_at=start,
        delay_seconds=20,
    )

    post_event(event)


# ------------------------------------------------------------------
# SCENARIO 4: INVALID RANGE HR
# Expected:
# - validationStatus = invalid
# ------------------------------------------------------------------
def scenario_invalid_range_hr():
    start = datetime.now(timezone.utc)
    patient_id = "fail_badhr_001"

    event = build_event(
        patient_id=patient_id,
        metric_type="heart_rate",
        value=500,
        unit="bpm",
        recorded_at=start,
        delay_seconds=3,
    )

    post_event(event)


# ------------------------------------------------------------------
# SCENARIO 5: INVALID RANGE SPO2
# Expected:
# - validationStatus = invalid
# ------------------------------------------------------------------
def scenario_invalid_range_spo2():
    start = datetime.now(timezone.utc)
    patient_id = "fail_badspo2_001"

    event = build_event(
        patient_id=patient_id,
        metric_type="spo2",
        value=40,
        unit="%",
        recorded_at=start,
        delay_seconds=3,
    )

    post_event(event)


# ------------------------------------------------------------------
# SCENARIO 6: DUPLICATE EVENT ID
# Expected:
# - first request succeeds
# - second request returns 409
# ------------------------------------------------------------------
def scenario_duplicate_event_id():
    start = datetime.now(timezone.utc)
    patient_id = "fail_dup_001"
    duplicate_id = "evt_duplicate_test_001"

    event1 = build_event(
        patient_id=patient_id,
        metric_type="heart_rate",
        value=90,
        unit="bpm",
        recorded_at=start,
        delay_seconds=3,
        event_id=duplicate_id,
    )

    event2 = build_event(
        patient_id=patient_id,
        metric_type="heart_rate",
        value=92,
        unit="bpm",
        recorded_at=start + timedelta(seconds=5),
        delay_seconds=3,
        event_id=duplicate_id,
    )

    print("First insert should succeed.")
    post_event(event1)

    print("Second insert should fail with duplicate eventId.")
    post_event(event2)


# ------------------------------------------------------------------
# SCENARIO 7: NO DATA
# Expected:
# - after a valid realtime event, if enough time passes with no new valid
#   realtime event, /check-no-data should return NO_DATA
#
# Notes:
# - easiest if backend NO_DATA threshold is temporarily set low (e.g. 15 sec)
# - or if you manually backdate DB before checking
# ------------------------------------------------------------------
def scenario_no_data(wait_seconds: int = 20):
    start = datetime.now(timezone.utc)
    patient_id = "fail_nodata_001"

    event = build_event(
        patient_id=patient_id,
        metric_type="heart_rate",
        value=88,
        unit="bpm",
        recorded_at=start,
        delay_seconds=3,
    )

    print("Sending initial valid realtime event...")
    post_event(event)

    print(f"Waiting {wait_seconds} seconds before checking no-data condition...")
    time.sleep(wait_seconds)

    check_no_data(patient_id)


# ------------------------------------------------------------------
# SCENARIO 8: MIXED FAILURE PACK
# ------------------------------------------------------------------
def scenario_all_failures():
    scenario_valid_realtime()
    time.sleep(0.5)

    scenario_delayed_usable()
    time.sleep(0.5)

    scenario_invalid_stale()
    time.sleep(0.5)

    scenario_invalid_range_hr()
    time.sleep(0.5)

    scenario_invalid_range_spo2()
    time.sleep(0.5)

    scenario_duplicate_event_id()
    time.sleep(0.5)

    # Use lower threshold in backend if you don't want to wait 60s
    scenario_no_data(wait_seconds=20)


if __name__ == "__main__":
    print("Choose Day 18 scenario:")
    print("1 - valid_realtime")
    print("2 - delayed_usable")
    print("3 - invalid_stale")
    print("4 - invalid_range_hr")
    print("5 - invalid_range_spo2")
    print("6 - duplicate_event_id")
    print("7 - no_data")
    print("8 - all_failures")

    choice = input("Enter choice: ").strip()

    if choice == "1":
        run_scenario("VALID_REALTIME", scenario_valid_realtime)
    elif choice == "2":
        run_scenario("DELAYED_USABLE", scenario_delayed_usable)
    elif choice == "3":
        run_scenario("INVALID_STALE", scenario_invalid_stale)
    elif choice == "4":
        run_scenario("INVALID_RANGE_HR", scenario_invalid_range_hr)
    elif choice == "5":
        run_scenario("INVALID_RANGE_SPO2", scenario_invalid_range_spo2)
    elif choice == "6":
        run_scenario("DUPLICATE_EVENT_ID", scenario_duplicate_event_id)
    elif choice == "7":
        run_scenario("NO_DATA", scenario_no_data)
    elif choice == "8":
        run_scenario("ALL_FAILURES", scenario_all_failures)
    else:
        print("Invalid choice.")