import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.reminders.enums import ActorRole, ReminderActionType, ReminderState
from app.reminders.models.reminder_action_log import ReminderActionLog
from app.reminders.models.reminder_occurrence import ReminderOccurrence

class ReminderSchedulerService:
    @staticmethod
    def _log_transition(
        db: Session,
        occurrence_id: str,
        action_type: ReminderActionType,
        from_state: ReminderState | None,
        to_state: ReminderState | None,
        metadata_json: str | None = None,
    ) -> None:
        db.add(
            ReminderActionLog(
                id=f"ral_{uuid.uuid4().hex[:12]}",
                occurrence_id=occurrence_id,
                actor_role=ActorRole.SYSTEM,
                actor_id=None,
                action_type=action_type,
                from_state=from_state,
                to_state=to_state,
                metadata_json=metadata_json,
            )
        )

    @staticmethod
    def run_due_and_missed_transition_pass(db: Session) -> dict:
        now = datetime.now(timezone.utc)

        upcoming_to_due = 0
        snoozed_to_due = 0
        due_to_missed = 0
        snoozed_to_missed = 0

        upcoming_rows = (
            db.query(ReminderOccurrence)
            .filter(ReminderOccurrence.state == ReminderState.UPCOMING)
            .filter(ReminderOccurrence.due_at <= now)
            .all()
        )

        for row in upcoming_rows:
            from_state = row.state
            row.state = ReminderState.DUE
            row.state_changed_at = now

            ReminderSchedulerService._log_transition(
                db=db,
                occurrence_id=row.id,
                action_type=ReminderActionType.DUE,
                from_state=from_state,
                to_state=ReminderState.DUE,
            )
            upcoming_to_due += 1

        snoozed_due_rows = (
            db.query(ReminderOccurrence)
            .filter(ReminderOccurrence.state == ReminderState.SNOOZED)
            .filter(ReminderOccurrence.snooze_until.isnot(None))
            .filter(ReminderOccurrence.snooze_until <= now)
            .filter(ReminderOccurrence.miss_deadline_at > now)
            .all()
        )

        for row in snoozed_due_rows:
            from_state = row.state
            row.state = ReminderState.DUE
            row.state_changed_at = now

            ReminderSchedulerService._log_transition(
                db=db,
                occurrence_id=row.id,
                action_type=ReminderActionType.DUE,
                from_state=from_state,
                to_state=ReminderState.DUE,
            )
            snoozed_to_due += 1

        due_missed_rows = (
            db.query(ReminderOccurrence)
            .filter(ReminderOccurrence.state == ReminderState.DUE)
            .filter(ReminderOccurrence.miss_deadline_at <= now)
            .all()
        )

        for row in due_missed_rows:
            from_state = row.state
            row.state = ReminderState.MISSED
            row.missed_at = now
            row.state_changed_at = now

            ReminderSchedulerService._log_transition(
                db=db,
                occurrence_id=row.id,
                action_type=ReminderActionType.MISSED,
                from_state=from_state,
                to_state=ReminderState.MISSED,
            )
            due_to_missed += 1

        snoozed_missed_rows = (
            db.query(ReminderOccurrence)
            .filter(ReminderOccurrence.state == ReminderState.SNOOZED)
            .filter(ReminderOccurrence.miss_deadline_at <= now)
            .all()
        )

        for row in snoozed_missed_rows:
            from_state = row.state
            row.state = ReminderState.MISSED
            row.missed_at = now
            row.state_changed_at = now

            ReminderSchedulerService._log_transition(
                db=db,
                occurrence_id=row.id,
                action_type=ReminderActionType.MISSED,
                from_state=from_state,
                to_state=ReminderState.MISSED,
            )
            snoozed_to_missed += 1

        db.commit()

        return {
            "ran_at": now.isoformat(),
            "upcoming_to_due": upcoming_to_due,
            "snoozed_to_due": snoozed_to_due,
            "due_to_missed": due_to_missed,
            "snoozed_to_missed": snoozed_to_missed,
            "total_changed": (
                upcoming_to_due
                + snoozed_to_due
                + due_to_missed
                + snoozed_to_missed
            ),
        }