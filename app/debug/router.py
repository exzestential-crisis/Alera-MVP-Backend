from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db, engine, DATABASE_URL
from app.alerts.models.raw_event import RawEvent
from app.alerts.models.condition_tracker import ConditionTracker
from app.alerts.models.patient_state import PatientState
from app.alerts.models.alert_occurrence import Occurrence

router = APIRouter()


@router.get("/db-info")
def debug_db_info():
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT current_database(), current_user, current_schema()")
        ).fetchone()

    return {
        "database_url": DATABASE_URL,
        "current_database": row[0],
        "current_user": row[1],
        "current_schema": row[2],
    }


@router.get("/db-counts")
def debug_db_counts(db: Session = Depends(get_db)):
    return {
        "raw_events": db.query(RawEvent).count(),
        "condition_trackers": db.query(ConditionTracker).count(),
        "patient_states": db.query(PatientState).count(),
        "occurrences": db.query(Occurrence).count(),
    }