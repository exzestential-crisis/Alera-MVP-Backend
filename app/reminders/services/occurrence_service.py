import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.reminders.enums import ReminderSection, ReminderState
from app.reminders.models.reminder_occurrence import ReminderOccurrence


DEFAULT_MISS_WINDOW_MINUTES = 30


class ReminderOccurrenceService:
    @staticmethod
    def create_occurrence(
        db: Session,
        template_id: str,
        patient_id: str,
        scheduled_at: datetime,
    ) -> ReminderOccurrence:
        if scheduled_at.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")

        occurrence = ReminderOccurrence(
            id=f"ro_{uuid.uuid4().hex[:12]}",
            template_id=template_id,
            patient_id=patient_id,
            scheduled_at=scheduled_at,
            due_at=scheduled_at,
            miss_deadline_at=scheduled_at + timedelta(minutes=DEFAULT_MISS_WINDOW_MINUTES),
            state=ReminderState.UPCOMING,
            state_changed_at=datetime.now(timezone.utc),
        )
        db.add(occurrence)
        db.commit()
        db.refresh(occurrence)
        return occurrence

    @staticmethod
    def list_occurrences(db: Session):
        return db.query(ReminderOccurrence).order_by(ReminderOccurrence.scheduled_at.asc()).all()

    @staticmethod
    def get_occurrence(db: Session, occurrence_id: str) -> ReminderOccurrence | None:
        return db.query(ReminderOccurrence).filter(ReminderOccurrence.id == occurrence_id).first()

    @staticmethod
    def get_occurrence_or_raise(db: Session, occurrence_id: str) -> ReminderOccurrence:
        occurrence = db.query(ReminderOccurrence).filter(ReminderOccurrence.id == occurrence_id).first()
        if not occurrence:
            raise ValueError("Occurrence not found")
        return occurrence
    
    @staticmethod
    def list_occurrences(
        db: Session,
        patient_id: str | None = None,
        state: ReminderState | None = None,
        section: ReminderSection | None = None,
    ):
        query = db.query(ReminderOccurrence)

        if patient_id:
            query = query.filter(ReminderOccurrence.patient_id == patient_id)

        if state:
            return (
                query.filter(ReminderOccurrence.state == state)
                .order_by(ReminderOccurrence.scheduled_at.asc())
                .all()
            )

        if section == ReminderSection.UPCOMING:
            return (
                query.filter(ReminderOccurrence.state == ReminderState.UPCOMING)
                .order_by(ReminderOccurrence.scheduled_at.asc())
                .all()
            )

        if section == ReminderSection.HISTORY:
            return (
                query.filter(
                    ReminderOccurrence.state.in_(
                        [ReminderState.COMPLETED, ReminderState.MISSED]
                    )
                )
                .order_by(ReminderOccurrence.updated_at.desc())
                .all()
            )

        if section == ReminderSection.ACTIVE:
            rows = (
                query.filter(
                    ReminderOccurrence.state.in_(
                        [ReminderState.MISSED, ReminderState.DUE, ReminderState.SNOOZED]
                    )
                )
                .all()
            )

            priority = {
                ReminderState.MISSED: 0,
                ReminderState.DUE: 1,
                ReminderState.SNOOZED: 2,
            }

            return sorted(
                rows,
                key=lambda row: (
                    priority[row.state],
                    row.scheduled_at,
                ),
            )

        return query.order_by(ReminderOccurrence.scheduled_at.asc()).all()