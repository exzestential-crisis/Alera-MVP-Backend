from enum import Enum


class ReminderCategory(str, Enum):
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    DAILY_HABIT = "daily_habit"
    MOBILITY_ACTIVITY = "mobility_activity"
    MONITORING = "monitoring"
    CHECK_IN = "check_in"


class ReminderState(str, Enum):
    UPCOMING = "UPCOMING"
    DUE = "DUE"
    SNOOZED = "SNOOZED"
    COMPLETED = "COMPLETED"
    MISSED = "MISSED"


class RecurrenceType(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class ActorRole(str, Enum):
    SYSTEM = "system"
    PATIENT = "patient"
    CAREGIVER = "caregiver"


class ReminderActionType(str, Enum):
    CREATED = "created"
    GENERATED = "generated"
    DUE = "due"
    SNOOZED = "snoozed"
    MARKED_TAKEN = "marked_taken"
    MISSED = "missed"
    RESCHEDULED = "rescheduled"
    NOTE_ADDED = "note_added"
    CALL_LOGGED = "call_logged"
    MESSAGE_LOGGED = "message_logged"
    RESOLVED = "resolved"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DEACTIVATED = "template_deactivated"


class ReminderSection(str, Enum):
    ACTIVE = "active"
    UPCOMING = "upcoming"
    HISTORY = "history"