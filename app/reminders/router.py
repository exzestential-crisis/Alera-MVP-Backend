from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.reminders.enums import ReminderSection, ReminderState
from app.reminders.schemas.action_schema import (
    AddNoteRequest,
    MarkTakenRequest,
    ResolveMissedRequest,
    RescheduleRequest,
    SnoozeRequest,
)
from app.reminders.schemas.log_schema import ReminderActionLogResponse
from app.reminders.schemas.note_schema import ReminderNoteResponse
from app.reminders.schemas.occurrence_schema import (
    ManualOccurrenceCreate,
    ReminderOccurrenceResponse,
)
from app.reminders.schemas.template_schema import (
    ReminderTemplateCreate,
    ReminderTemplateResponse,
)
from app.reminders.schemas.scheduler_schema import SchedulerRunResponse
from app.reminders.services.action_service import ReminderActionService
from app.reminders.services.occurrence_service import ReminderOccurrenceService
from app.reminders.services.template_service import ReminderTemplateService
from app.reminders.services.scheduler_service import ReminderSchedulerService


router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("/templates", response_model=ReminderTemplateResponse)
def create_template(payload: ReminderTemplateCreate, db: Session = Depends(get_db)):
    return ReminderTemplateService.create_template(db, payload)


@router.get("/templates", response_model=list[ReminderTemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    return ReminderTemplateService.list_templates(db)


@router.post("/occurrences/manual", response_model=ReminderOccurrenceResponse)
def create_manual_occurrence(
    payload: ManualOccurrenceCreate,
    db: Session = Depends(get_db),
):
    try:
        return ReminderOccurrenceService.create_occurrence(
            db=db,
            template_id=payload.template_id,
            patient_id=payload.patient_id,
            scheduled_at=payload.scheduled_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/occurrences", response_model=list[ReminderOccurrenceResponse])
def list_occurrences(
    patient_id: Optional[str] = None,
    state: Optional[ReminderState] = None,
    section: Optional[ReminderSection] = None,
    db: Session = Depends(get_db),
):
    return ReminderOccurrenceService.list_occurrences(
        db=db,
        patient_id=patient_id,
        state=state,
        section=section,
    )

@router.post("/occurrences/{occurrence_id}/snooze", response_model=ReminderOccurrenceResponse)
def snooze_occurrence(
    occurrence_id: str,
    payload: SnoozeRequest,
    db: Session = Depends(get_db),
):
    occurrence = ReminderOccurrenceService.get_occurrence(db, occurrence_id)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")

    try:
        return ReminderActionService.snooze(
            db=db,
            occurrence=occurrence,
            actor_id=payload.actor_id,
            minutes=payload.minutes,
            actor_role=payload.actor_role,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/occurrences/{occurrence_id}/mark-taken", response_model=ReminderOccurrenceResponse)
def mark_taken_occurrence(
    occurrence_id: str,
    payload: MarkTakenRequest,
    db: Session = Depends(get_db),
):
    occurrence = ReminderOccurrenceService.get_occurrence(db, occurrence_id)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")

    try:
        return ReminderActionService.mark_taken(
            db=db,
            occurrence=occurrence,
            actor_id=payload.actor_id,
            actor_role=payload.actor_role,
            note=payload.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/occurrences/{occurrence_id}", response_model=ReminderOccurrenceResponse)
def get_occurrence(occurrence_id: str, db: Session = Depends(get_db)):
    occurrence = ReminderOccurrenceService.get_occurrence(db, occurrence_id)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    return occurrence


@router.get("/occurrences/{occurrence_id}/logs", response_model=list[ReminderActionLogResponse])
def list_occurrence_logs(occurrence_id: str, db: Session = Depends(get_db)):
    occurrence = ReminderOccurrenceService.get_occurrence(db, occurrence_id)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    return ReminderActionService.list_logs_for_occurrence(db, occurrence_id)


@router.post("/templates/{template_id}/deactivate", response_model=ReminderTemplateResponse)
def deactivate_template(template_id: str, db: Session = Depends(get_db)):
    try:
        return ReminderTemplateService.deactivate_template(db, template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.post("/occurrences/{occurrence_id}/notes", response_model=ReminderNoteResponse)
def add_note_to_occurrence(
    occurrence_id: str,
    payload: AddNoteRequest,
    db: Session = Depends(get_db),
):
    occurrence = ReminderOccurrenceService.get_occurrence(db, occurrence_id)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")

    try:
        return ReminderActionService.add_note(
            db=db,
            occurrence=occurrence,
            actor_id=payload.actor_id,
            actor_role=payload.actor_role,
            text=payload.text,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/occurrences/{occurrence_id}/notes", response_model=list[ReminderNoteResponse])
def list_occurrence_notes(occurrence_id: str, db: Session = Depends(get_db)):
    occurrence = ReminderOccurrenceService.get_occurrence(db, occurrence_id)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    return ReminderActionService.list_notes_for_occurrence(db, occurrence_id)


@router.post("/occurrences/{occurrence_id}/resolve-missed", response_model=ReminderOccurrenceResponse)
def resolve_missed_occurrence(
    occurrence_id: str,
    payload: ResolveMissedRequest,
    db: Session = Depends(get_db),
):
    occurrence = ReminderOccurrenceService.get_occurrence(db, occurrence_id)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")

    try:
        return ReminderActionService.resolve_missed(
            db=db,
            occurrence=occurrence,
            actor_id=payload.actor_id,
            actor_role=payload.actor_role,
            note=payload.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/occurrences/{occurrence_id}/reschedule", response_model=ReminderOccurrenceResponse)
def reschedule_occurrence(
    occurrence_id: str,
    payload: RescheduleRequest,
    db: Session = Depends(get_db),
):
    occurrence = ReminderOccurrenceService.get_occurrence(db, occurrence_id)
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")

    try:
        return ReminderActionService.reschedule(
            db=db,
            occurrence=occurrence,
            actor_id=payload.actor_id,
            actor_role=payload.actor_role,
            new_scheduled_at=payload.new_scheduled_at,
            reason=payload.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scheduler/run", response_model=SchedulerRunResponse)
def run_scheduler_pass(db: Session = Depends(get_db)):
    return ReminderSchedulerService.run_due_and_missed_transition_pass(db)