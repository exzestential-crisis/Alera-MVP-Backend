from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.condition_tracker import ConditionTracker
from app.services.persistence_service import update_and_check_persistence


def make_test_db():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_first_abnormal_event_starts_tracker():
    db = make_test_db()
    try:
        event_time = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)

        result = update_and_check_persistence(
            db=db,
            patient_id="p1",
            condition_key="HR_HIGH_WARNING",
            event_time=event_time,
        )

        assert result["persistenceConfirmed"] is False
        assert result["justConfirmed"] is False
        assert result["elapsedSeconds"] == 0.0
    finally:
        db.close()


def test_hr_warning_confirms_at_30_seconds():
    db = make_test_db()
    try:
        t0 = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
        t1 = t0 + timedelta(seconds=10)
        t2 = t0 + timedelta(seconds=30)

        r1 = update_and_check_persistence(db, "p1", "HR_HIGH_WARNING", t0)
        r2 = update_and_check_persistence(db, "p1", "HR_HIGH_WARNING", t1)
        r3 = update_and_check_persistence(db, "p1", "HR_HIGH_WARNING", t2)

        assert r1["persistenceConfirmed"] is False
        assert r2["persistenceConfirmed"] is False
        assert r3["persistenceConfirmed"] is True
        assert r3["justConfirmed"] is True
    finally:
        db.close()


def test_immediate_critical_just_confirms_once():
    db = make_test_db()
    try:
        t0 = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)
        t1 = t0 + timedelta(seconds=5)

        r1 = update_and_check_persistence(db, "p1", "SPO2_LOW_CRITICAL", t0)
        r2 = update_and_check_persistence(db, "p1", "SPO2_LOW_CRITICAL", t1)

        assert r1["persistenceConfirmed"] is True
        assert r1["justConfirmed"] is True

        assert r2["persistenceConfirmed"] is True
        assert r2["justConfirmed"] is False
    finally:
        db.close()