"""
Email Repository Layer
======================
Handles database interactions for email log tracking and queue state lookups.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.models.email_log_model import EmailLogModel
from backend.app.schemas.email_schema import EmailLogCreate, EmailLogUpdate


class EmailRepository:
    """
    Encapsulates database operations for Email Logs, decoupling SQL queries from service logic.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, schema: EmailLogCreate) -> EmailLogModel:
        """Create a new Email Log record."""
        db_obj = EmailLogModel(
            evidence_id=schema.evidence_id,
            violation_id=schema.violation_id,
            recipient=schema.recipient,
            subject=schema.subject,
            body_html=schema.body_html,
            body_text=schema.body_text,
            status=schema.status,
            retry_count=schema.retry_count,
            error_message=schema.error_message
        )
        self.db.add(db_obj)
        self.db.flush()
        return db_obj

    def get(self, id: int) -> Optional[EmailLogModel]:
        """Fetch an email log record by primary key."""
        return self.db.query(EmailLogModel).filter(EmailLogModel.id == id).first()

    def update(self, id: int, schema: EmailLogUpdate) -> Optional[EmailLogModel]:
        """Update email log delivery status, retry counters, or errors."""
        db_obj = self.get(id)
        if not db_obj:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(db_obj, key, val)

        self.db.flush()
        return db_obj

    def get_pending_queue(self, max_retries: int = 3) -> List[EmailLogModel]:
        """
        Retrieves all logs with status 'pending' or 'retrying'
        where the retry count has not exceeded the maximum limit.
        """
        return self.db.query(EmailLogModel).filter(
            EmailLogModel.status.in_(["pending", "retrying"]),
            EmailLogModel.retry_count < max_retries
        ).order_by(EmailLogModel.created_at.asc()).all()

    def get_logs_by_recipient(self, recipient: str) -> List[EmailLogModel]:
        """Query email logs by recipient address."""
        return self.db.query(EmailLogModel).filter(
            EmailLogModel.recipient == recipient
        ).order_by(EmailLogModel.created_at.desc()).all()
