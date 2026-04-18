from datetime import datetime, timedelta, timezone
import time
import uuid
import requests

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

    print("-" * 100)
    print(
        f"{event['patientId']} | "
        f"{event['metric']['type']}={event['metric']['value']}{event['metric']['unit']} | "
        f"recordedAt={event['timestamp']['recordedAt']} | "
        f"delay={(datetime.fromisoformat(event['timestamp']['receivedAt'].replace('Z', '+00:00')) - datetime.fromisoformat(event['timestamp']['recordedAt'].replace('Z', '+00:00'))).total_seconds()}s"
    )
    print(
        f"validation={data.get('validationStatus')} | "
        f"threshold={data.get('thresholdViolated')} | "
        f"conditions={data.get('candidateConditions')} | "
        f"persisted={data.get('persistenceConfirmed')} | "
        f"state={data.get('state')} | "
        f"transition={data.get('stateTransition')} | "
        f"occurrence={data.get('occurrenceCreated')} | "
        f"occurrenceConditions={data.get('occurrenceConditions')}"
    )
    return data


def run_sequence(name: str, events: list[dict], sleep_seconds: float = 0.35):
    print("\n" + "=" * 100)
    print(f"RUNNING SCENARIO: {name}")
    print("=" * 100)
    results = []
    for event in events:
        data = send_event(event)
        results.append(data)
        time.sleep(sleep_seconds)
    return results


# ------------------------------------------------------------------
# DAY 17 SCENARIO 1: THRESHOLD EDGE VALUES
# ------------------------------------------------------------------
def scenario_day17_edges():
    start = datetime.now(timezone.utc)

    events = [
        # HR edges
        build_event("edge_hr_001", "heart_rate", 110, "bpm", start + timedelta(seconds=0)),
        build_event("edge_hr_002", "heart_rate", 111, "bpm", start + timedelta(seconds=10)),
        build_event("edge_hr_003", "heart_rate", 130, "bpm", start + timedelta(seconds=20)),
        build_event("edge_hr_004", "heart_rate", 131, "bpm", start + timedelta(seconds=30)),

        # SpO2 edges
        build_event("edge_spo2_001", "spo2", 92, "%", start + timedelta(seconds=40)),
        build_event("edge_spo2_002", "spo2", 91, "%", start + timedelta(seconds=50)),
        build_event("edge_spo2_003", "spo2", 90, "%", start + timedelta(seconds=60)),
        build_event("edge_spo2_004", "spo2", 89, "%", start + timedelta(seconds=70)),
    ]

    return run_sequence("DAY17_EDGES", events)


# ------------------------------------------------------------------
# DAY 17 SCENARIO 2: RAPID FLUCTUATION
# ------------------------------------------------------------------
def scenario_day17_fluctuation():
    start = datetime.now(timezone.utc)
    patient_id = "fluct_hr_001"

    events = [
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=0)),
        build_event(patient_id, "heart_rate", 109, "bpm", start + timedelta(seconds=10)),
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=20)),
        build_event(patient_id, "heart_rate", 109, "bpm", start + timedelta(seconds=30)),
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=40)),
    ]

    return run_sequence("DAY17_FLUCTUATION", events)


# ------------------------------------------------------------------
# DAY 17 SCENARIO 3: PERSISTENCE RESET / RE-ENTRY
# ------------------------------------------------------------------
def scenario_day17_reset():
    start = datetime.now(timezone.utc)
    patient_id = "reset_hr_001"

    events = [
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=0)),
        build_event(patient_id, "heart_rate", 119, "bpm", start + timedelta(seconds=10)),
        build_event(patient_id, "heart_rate", 90, "bpm", start + timedelta(seconds=20)),
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=30)),
        build_event(patient_id, "heart_rate", 119, "bpm", start + timedelta(seconds=40)),
        build_event(patient_id, "heart_rate", 121, "bpm", start + timedelta(seconds=60)),
    ]

    return run_sequence("DAY17_RESET", events)


# ------------------------------------------------------------------
# DAY 17 SCENARIO 4: DELAYED DATA
# ------------------------------------------------------------------
def scenario_day17_delayed():
    start = datetime.now(timezone.utc)
    patient_id = "delay_hr_001"

    events = [
        # First create an active warning tracker with realtime-valid events
        build_event(patient_id, "heart_rate", 118, "bpm", start + timedelta(seconds=0), delay_seconds=3),
        build_event(patient_id, "heart_rate", 119, "bpm", start + timedelta(seconds=10), delay_seconds=3),

        # Delayed abnormal event: should be delayed_usable, no realtime threshold handling
        build_event(patient_id, "heart_rate", 140, "bpm", start + timedelta(seconds=20), delay_seconds=10),

        # Delayed normal event: should NOT reset active realtime tracker
        build_event(patient_id, "heart_rate", 90, "bpm", start + timedelta(seconds=30), delay_seconds=10),

        # Realtime event again so you can observe whether tracker was incorrectly reset
        build_event(patient_id, "heart_rate", 121, "bpm", start + timedelta(seconds=40), delay_seconds=3),
    ]

    return run_sequence("DAY17_DELAYED", events)


# ------------------------------------------------------------------
# RUN ALL DAY 17 SCENARIOS
# ------------------------------------------------------------------
def scenario_day17_all():
    scenario_day17_edges()
    scenario_day17_fluctuation()
    scenario_day17_reset()
    scenario_day17_delayed()


if __name__ == "__main__":
    print("Choose scenario:")
    print("1 - day17_edges")
    print("2 - day17_fluctuation")
    print("3 - day17_reset")
    print("4 - day17_delayed")
    print("5 - day17_all")

    choice = input("Enter choice: ").strip()

    if choice == "1":
        scenario_day17_edges()
    elif choice == "2":
        scenario_day17_fluctuation()
    elif choice == "3":
        scenario_day17_reset()
    elif choice == "4":
        scenario_day17_delayed()
    elif choice == "5":
        scenario_day17_all()
    else:
        print("Invalid choice.")