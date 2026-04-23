import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.reminders.enums import ActorRole, ReminderActionType, ReminderState
from app.reminders.models.reminder_action_log import ReminderActionLog
from app.reminders.models.reminder_note import ReminderNote
from app.reminders.models.reminder_occurrence import ReminderOccurrence
from app.reminders.services.fsm_service import ReminderFSMService


DEFAULT_MISS_WINDOW_MINUTES = 30


class ReminderActionService:
    @staticmethod
    def _log(
        db: Session,
        occurrence_id: str,
        actor_role: ActorRole,
        actor_id: str | None,
        action_type: ReminderActionType,
        from_state: ReminderState | None,
        to_state: ReminderState | None,
        metadata_json: str | None = None,
    ) -> None:
        log = ReminderActionLog(
            id=f"ral_{uuid.uuid4().hex[:12]}",
            occurrence_id=occurrence_id,
            actor_role=actor_role,
            actor_id=actor_id,
            action_type=action_type,
            from_state=from_state,
            to_state=to_state,
            metadata_json=metadata_json,
        )
        db.add(log)

    @staticmethod
    def list_logs_for_occurrence(db: Session, occurrence_id: str):
        return (
            db.query(ReminderActionLog)
            .filter(ReminderActionLog.occurrence_id == occurrence_id)
            .order_by(ReminderActionLog.action_at.asc())
            .all()
        )

    @staticmethod
    def list_notes_for_occurrence(db: Session, occurrence_id: str):
        return (
            db.query(ReminderNote)
            .filter(ReminderNote.occurrence_id == occurrence_id)
            .order_by(ReminderNote.created_at.asc())
            .all()
        )

    @staticmethod
    def snooze(
        db: Session,
        occurrence: ReminderOccurrence,
        actor_id: str,
        actor_role: ActorRole,
        minutes: int,
    ) -> ReminderOccurrence:
        if actor_role not in {ActorRole.PATIENT, ActorRole.CAREGIVER}:
            raise ValueError("Invalid actor role for snooze")

        if not ReminderFSMService.can_snooze(occurrence.state):
            raise ValueError(f"Cannot snooze occurrence in state {occurrence.state}")

        now = datetime.now(timezone.utc)
        from_state = occurrence.state

        occurrence.state = ReminderState.SNOOZED
        occurrence.snooze_until = now + timedelta(minutes=minutes)
        occurrence.state_changed_at = now

        ReminderActionService._log(
            db=db,
            occurrence_id=occurrence.id,
            actor_role=actor_role,
            actor_id=actor_id,
            action_type=ReminderActionType.SNOOZED,
            from_state=from_state,
            to_state=ReminderState.SNOOZED,
            metadata_json=json.dumps({"minutes": minutes}),
        )

        db.commit()
        db.refresh(occurrence)
        return occurrence

    @staticmethod
    def mark_taken(
        db: Session,
        occurrence: ReminderOccurrence,
        actor_id: str,
        actor_role: ActorRole,
        note: str | None = None,
    ) -> ReminderOccurrence:
        if actor_role not in {ActorRole.PATIENT, ActorRole.CAREGIVER}:
            raise ValueError("Invalid actor role for mark taken")

        if not ReminderFSMService.can_mark_taken(occurrence.state):
            raise ValueError(f"Cannot mark taken from state {occurrence.state}")

        now = datetime.now(timezone.utc)
        from_state = occurrence.state

        occurrence.state = ReminderState.COMPLETED
        occurrence.completed_at = now
        occurrence.state_changed_at = now
        occurrence.completion_actor_role = actor_role
        occurrence.override_marked_taken = (
            from_state == ReminderState.MISSED and actor_role == ActorRole.CAREGIVER
        )

        ReminderActionService._log(
            db=db,
            occurrence_id=occurrence.id,
            actor_role=actor_role,
            actor_id=actor_id,
            action_type=ReminderActionType.MARKED_TAKEN,
            from_state=from_state,
            to_state=ReminderState.COMPLETED,
            metadata_json=None,
        )

        if note:
            db.add(
                ReminderNote(
                    id=f"rn_{uuid.uuid4().hex[:12]}",
                    occurrence_id=occurrence.id,
                    author_role=actor_role,
                    author_id=actor_id,
                    note_text=note,
                )
            )

        db.commit()
        db.refresh(occurrence)
        return occurrence

    @staticmethod
    def add_note(
        db: Session,
        occurrence: ReminderOccurrence,
        actor_id: str,
        actor_role: ActorRole,
        text: str,
    ) -> ReminderNote:
        if actor_role != ActorRole.CAREGIVER:
            raise ValueError("Only caregiver can add notes in MVP")

        note = ReminderNote(
            id=f"rn_{uuid.uuid4().hex[:12]}",
            occurrence_id=occurrence.id,
            author_role=actor_role,
            author_id=actor_id,
            note_text=text,
        )
        db.add(note)

        ReminderActionService._log(
            db=db,
            occurrence_id=occurrence.id,
            actor_role=actor_role,
            actor_id=actor_id,
            action_type=ReminderActionType.NOTE_ADDED,
            from_state=occurrence.state,
            to_state=occurrence.state,
            metadata_json=json.dumps({"text": text}),
        )

        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def resolve_missed(
        db: Session,
        occurrence: ReminderOccurrence,
        actor_id: str,
        actor_role: ActorRole,
        note: str | None = None,
    ) -> ReminderOccurrence:
        if actor_role != ActorRole.CAREGIVER:
            raise ValueError("Only caregiver can resolve missed occurrences")

        if occurrence.state != ReminderState.MISSED:
            raise ValueError("Only MISSED occurrences can be operationally resolved")

        occurrence.resolved_at = datetime.now(timezone.utc)
        occurrence.resolved_by = actor_id

        ReminderActionService._log(
            db=db,
            occurrence_id=occurrence.id,
            actor_role=actor_role,
            actor_id=actor_id,
            action_type=ReminderActionType.RESOLVED,
            from_state=occurrence.state,
            to_state=occurrence.state,
            metadata_json=json.dumps({"note": note}) if note else None,
        )

        if note:
            db.add(
                ReminderNote(
                    id=f"rn_{uuid.uuid4().hex[:12]}",
                    occurrence_id=occurrence.id,
                    author_role=actor_role,
                    author_id=actor_id,
                    note_text=note,
                )
            )

        db.commit()
        db.refresh(occurrence)
        return occurrence

    @staticmethod
    def reschedule(
        db: Session,
        occurrence: ReminderOccurrence,
        actor_id: str,
        actor_role: ActorRole,
        new_scheduled_at: datetime,
        reason: str | None = None,
    ) -> ReminderOccurrence:
        if actor_role != ActorRole.CAREGIVER:
            raise ValueError("Only caregiver can reschedule occurrences")

        if not ReminderFSMService.can_reschedule(occurrence.state):
            raise ValueError(f"Cannot reschedule occurrence in state {occurrence.state}")

        if new_scheduled_at.tzinfo is None:
            raise ValueError("new_scheduled_at must be timezone-aware")

        now = datetime.now(timezone.utc)

        new_occurrence = ReminderOccurrence(
            id=f"ro_{uuid.uuid4().hex[:12]}",
            template_id=occurrence.template_id,
            patient_id=occurrence.patient_id,
            scheduled_at=new_scheduled_at,
            due_at=new_scheduled_at,
            miss_deadline_at=new_scheduled_at + timedelta(minutes=DEFAULT_MISS_WINDOW_MINUTES),
            state=ReminderState.UPCOMING,
            state_changed_at=now,
        )
        db.add(new_occurrence)
        db.flush()

        ReminderActionService._log(
            db=db,
            occurrence_id=occurrence.id,
            actor_role=actor_role,
            actor_id=actor_id,
            action_type=ReminderActionType.RESCHEDULED,
            from_state=occurrence.state,
            to_state=occurrence.state,
            metadata_json=json.dumps(
                {
                    "new_occurrence_id": new_occurrence.id,
                    "old_scheduled_at": occurrence.scheduled_at.isoformat(),
                    "new_scheduled_at": new_scheduled_at.isoformat(),
                    "reason": reason,
                }
            ),
        )

        ReminderActionService._log(
            db=db,
            occurrence_id=new_occurrence.id,
            actor_role=ActorRole.SYSTEM,
            actor_id=None,
            action_type=ReminderActionType.GENERATED,
            from_state=None,
            to_state=ReminderState.UPCOMING,
            metadata_json=json.dumps(
                {
                    "source_occurrence_id": occurrence.id,
                    "reason": reason,
                }
            ),
        )

        if reason:
            db.add(
                ReminderNote(
                    id=f"rn_{uuid.uuid4().hex[:12]}",
                    occurrence_id=occurrence.id,
                    author_role=actor_role,
                    author_id=actor_id,
                    note_text=f"Rescheduled: {reason}",
                )
            )

        db.commit()
        db.refresh(new_occurrence)
        return new_occurrence