import uuid

from sqlalchemy.orm import Session

from app.reminders.models.reminder_template import ReminderTemplate
from app.reminders.schemas.template_schema import ReminderTemplateCreate


class ReminderTemplateService:
    @staticmethod
    def create_template(db: Session, payload: ReminderTemplateCreate) -> ReminderTemplate:
        template = ReminderTemplate(
            id=f"rt_{uuid.uuid4().hex[:12]}",
            patient_id=payload.patient_id,
            created_by=payload.created_by,
            category=payload.category,
            title=payload.title,
            description=payload.description,
            recurrence_type=payload.recurrence_type,
            recurrence_rule=payload.recurrence_rule,
            default_time=payload.default_time,
            timezone=payload.timezone,
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_active=True,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def list_templates(db: Session):
        return db.query(ReminderTemplate).order_by(ReminderTemplate.created_at.desc()).all()

    @staticmethod
    def deactivate_template(db: Session, template_id: str):
        template = db.query(ReminderTemplate).filter(ReminderTemplate.id == template_id).first()
        if not template:
            raise ValueError("Template not found")

        template.is_active = False
        db.commit()
        db.refresh(template)
        return template