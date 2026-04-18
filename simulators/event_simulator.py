import time
import uuid
import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:8000/events"


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_event(
    patient_id: str,
    metric_type: str,
    value: float,
    unit: str,
    recorded_at: datetime,
    delay_seconds: int = 3,
    device_id: str = "sim_watch_01",
):
    received_at = recorded_at + timedelta(seconds=delay_seconds)

    return {
        "eventId": f"evt_{uuid.uuid4().hex[:12]}",
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


def send_event(event: dict):
    response = requests.post(BASE_URL, json=event, timeout=10)
    response.raise_for_status()
    data = response.json()

    print("=" * 80)
    print(f"Sent: {event['eventId']}")
    print(f"Patient: {event['patientId']}")
    print(f"Metric: {event['metric']['type']} = {event['metric']['value']} {event['metric']['unit']}")
    print(f"RecordedAt: {event['timestamp']['recordedAt']}")
    print("--- Response ---")
    print(f"accepted: {data.get('accepted')}")
    print(f"validationStatus: {data.get('validationStatus')}")
    print(f"candidateConditions: {data.get('candidateConditions')}")
    print(f"persistenceConfirmed: {data.get('persistenceConfirmed')}")
    print(f"state: {data.get('state')}")
    print(f"stateTransition: {data.get('stateTransition')}")
    print(f"occurrenceCreated: {data.get('occurrenceCreated')}")
    print(f"occurrenceConditions: {data.get('occurrenceConditions')}")
    return data


def run_sequence(events: list[dict], sleep_seconds: float = 0.5):
    for event in events:
        send_event(event)
        time.sleep(sleep_seconds)


def scenario_normal(patient_id: str):
    start = datetime.now(timezone.utc)

    events = [
        build_event(patient_id, "heart_rate", 85, "bpm", start + timedelta(seconds=0)),
        build_event(patient_id, "heart_rate", 88, "bpm", start + timedelta(seconds=10)),
        build_event(patient_id, "spo2", 97, "%", start + timedelta(seconds=20)),
        build_event(patient_id, "spo2", 96, "%", start + timedelta(seconds=30)),
    ]
    run_sequence(events)


def scenario_warning(patient_id: str):
    start = datetime.now(timezone.utc)

    events = [
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=0)),
        build_event(patient_id, "heart_rate", 119, "bpm", start + timedelta(seconds=10)),
        build_event(patient_id, "heart_rate", 121, "bpm", start + timedelta(seconds=30)),
    ]
    run_sequence(events)


def scenario_critical(patient_id: str):
    start = datetime.now(timezone.utc)

    events = [
        build_event(patient_id, "spo2", 88, "%", start + timedelta(seconds=0)),
        build_event(patient_id, "spo2", 87, "%", start + timedelta(seconds=10)),
    ]
    run_sequence(events)


def scenario_recovery(patient_id: str):
    start = datetime.now(timezone.utc)

    events = [
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=0)),
        build_event(patient_id, "heart_rate", 119, "bpm", start + timedelta(seconds=10)),
        build_event(patient_id, "heart_rate", 121, "bpm", start + timedelta(seconds=30)),
        build_event(patient_id, "heart_rate", 90, "bpm", start + timedelta(seconds=40)),
        build_event(patient_id, "heart_rate", 88, "bpm", start + timedelta(seconds=50)),
    ]
    run_sequence(events)


def scenario_full_flow(patient_id: str):
    start = datetime.now(timezone.utc)

    events = [
        # normal
        build_event(patient_id, "heart_rate", 85, "bpm", start + timedelta(seconds=0)),
        build_event(patient_id, "spo2", 97, "%", start + timedelta(seconds=5)),

        # warning buildup
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=10)),
        build_event(patient_id, "heart_rate", 119, "bpm", start + timedelta(seconds=20)),
        build_event(patient_id, "heart_rate", 121, "bpm", start + timedelta(seconds=40)),

        # critical
        build_event(patient_id, "spo2", 88, "%", start + timedelta(seconds=50)),

        # recovery
        build_event(patient_id, "spo2", 96, "%", start + timedelta(seconds=60)),
        build_event(patient_id, "heart_rate", 90, "bpm", start + timedelta(seconds=70)),
    ]
    run_sequence(events)


if __name__ == "__main__":
    patient_id = "sim_patient_001"

    print("Choose scenario:")
    print("1 - normal")
    print("2 - warning")
    print("3 - critical")
    print("4 - recovery")
    print("5 - full_flow")

    choice = input("Enter choice: ").strip()

    if choice == "1":
        scenario_normal(patient_id)
    elif choice == "2":
        scenario_warning(patient_id)
    elif choice == "3":
        scenario_critical(patient_id)
    elif choice == "4":
        scenario_recovery(patient_id)
    elif choice == "5":
        scenario_full_flow(patient_id)
    else:
        print("Invalid choice.")