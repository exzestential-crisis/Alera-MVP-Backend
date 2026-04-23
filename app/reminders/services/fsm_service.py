from app.reminders.enums import ReminderState


class ReminderFSMService:
    @staticmethod
    def can_snooze(state: ReminderState) -> bool:
        return state in {ReminderState.DUE, ReminderState.SNOOZED}

    @staticmethod
    def can_mark_taken(state: ReminderState) -> bool:
        return state in {
            ReminderState.DUE,
            ReminderState.SNOOZED,
            ReminderState.MISSED,
        }

    @staticmethod
    def can_reschedule(state: ReminderState) -> bool:
        return state in {
            ReminderState.UPCOMING,
            ReminderState.DUE,
            ReminderState.SNOOZED,
            ReminderState.MISSED,
        }

    @staticmethod
    def is_terminal(state: ReminderState) -> bool:
        return state == ReminderState.COMPLETED