"""
Email Queue Service
===================
Manages database queue polling, connection reuse batches, retries, and transactional status updates.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger
import datetime
import time

from backend.app.config import settings
from backend.app.repositories.email_repository import EmailRepository
from backend.app.schemas.email_schema import EmailLogCreate, EmailLogUpdate
from backend.app.services.email_service import email_service
from backend.app.services.email_template_service import email_template_service
from backend.app.services.database_service import database_service


class EmailQueueService:
    """
    Service coordinating the email queue operations, retries, and database logging.
    """

    def __init__(self):
        self.max_retries = settings.EMAIL_MAX_RETRIES
        self.retry_delay = settings.EMAIL_RETRY_DELAY

    def queue_email(
        self,
        db: Session,
        recipient: str,
        subject: str,
        template_name: str,
        context_data: Dict[str, Any],
        evidence_id: Optional[str] = None,
        violation_id: Optional[str] = None
    ) -> Optional[EmailLogCreate]:
        """
        Renders HTML/text bodies and queues a new email notice in the database.
        """
        repo = EmailRepository(db)
        try:
            # Render HTML and text versions
            html_body, text_body = email_template_service.render(template_name, context_data)
            
            schema = EmailLogCreate(
                evidence_id=evidence_id,
                violation_id=violation_id,
                recipient=recipient,
                subject=subject,
                body_html=html_body,
                body_text=text_body,
                status="pending",
                retry_count=0
            )
            
            db_obj = repo.create(schema)
            logger.info(f"Email Queued: Subject '{subject}' for recipient {recipient}")
            return db_obj
        except Exception as e:
            logger.error(f"Failed to queue email: {e}")
            return None

    def process_queue(self, db: Session) -> int:
        """
        Processes all pending and retrying logs in the database.
        Uses connection reuse by opening one SMTP connection for the entire batch.
        """
        repo = EmailRepository(db)
        queue = repo.get_pending_queue(max_retries=self.max_retries)
        if not queue:
            return 0

        logger.info(f"Processing email queue: {len(queue)} messages found.")
        
        # Connect to SMTP server once for connection reuse
        server = None
        try:
            server = email_service.connect_smtp()
        except Exception as e:
            logger.error(f"Failed to establish SMTP connection for batch. Postponing: {e}")
            # Update status to retrying/failed depending on limits
            for log in queue:
                try:
                    new_retries = log.retry_count + 1
                    status = "retrying" if new_retries < self.max_retries else "failed"
                    repo.update(log.id, EmailLogUpdate(
                        status=status,
                        retry_count=new_retries,
                        error_message=f"SMTP Connection failure: {e}"
                    ))
                    db.commit()
                except Exception as db_err:
                    db.rollback()
                    logger.error(f"Failed to update log state during SMTP failure: {db_err}")
            return 0

        sent_count = 0
        for log in queue:
            # Determine attachments
            attachments = []
            if log.evidence_id:
                try:
                    evidence = database_service.fetch_evidence(log.evidence_id)
                    if evidence:
                        if evidence.original_frame_path:
                            attachments.append(evidence.original_frame_path)
                        if evidence.annotated_frame_path:
                            attachments.append(evidence.annotated_frame_path)
                        if evidence.vehicle_crop_path:
                            attachments.append(evidence.vehicle_crop_path)
                        if evidence.plate_crop_path:
                            attachments.append(evidence.plate_crop_path)
                except Exception as ev_err:
                    logger.error(f"Failed to fetch attachments for evidence {log.evidence_id}: {ev_err}")

            # Update status to sending
            try:
                repo.update(log.id, EmailLogUpdate(status="sending"))
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Transaction Rollback: Failed to mark log {log.id} as sending: {e}")
                continue

            # Attempt delivery
            success = False
            error_message = None
            
            # If retry attempt, log it
            if log.retry_count > 0:
                logger.info(f"Retry Attempt: Resending log {log.id} (attempt {log.retry_count + 1}/{self.max_retries})")

            try:
                success = email_service.send_with_connection(
                    server=server,
                    recipient=log.recipient,
                    subject=log.subject,
                    html_body=log.body_html,
                    text_body=log.body_text,
                    attachments=attachments
                )
                if not success:
                    error_message = "Delivery failed: SMTP send failed."
            except Exception as e:
                error_message = str(e)
                success = False

            # Commit status result
            try:
                if success:
                    repo.update(log.id, EmailLogUpdate(
                        status="sent",
                        error_message=None
                    ))
                    sent_count += 1
                else:
                    new_retries = log.retry_count + 1
                    status = "retrying" if new_retries < self.max_retries else "failed"
                    
                    if status == "failed":
                        logger.error(f"Email Failed: Max retries exceeded for email {log.id}. Error: {error_message}")
                    else:
                        logger.warning(f"Email Failed: Temp failure for email {log.id}. Retrying. Error: {error_message}")

                    repo.update(log.id, EmailLogUpdate(
                        status=status,
                        retry_count=new_retries,
                        error_message=error_message
                    ))
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Transaction Rollback: Failed to persist post-delivery status for log {log.id}: {e}")

        email_service.close_smtp(server)
        return sent_count

    def get_queue_statistics(self, db: Session) -> Dict[str, int]:
        """Calculates email queue statistics from the database."""
        from backend.app.models.email_log_model import EmailLogModel
        total = db.query(EmailLogModel).count()
        pending = db.query(EmailLogModel).filter(EmailLogModel.status.in_(["pending", "retrying"])).count()
        sent = db.query(EmailLogModel).filter(EmailLogModel.status == "sent").count()
        failed = db.query(EmailLogModel).filter(EmailLogModel.status == "failed").count()
        return {
            "total_emails": total,
            "pending_emails": pending,
            "sent_emails": sent,
            "failed_emails": failed
        }


# Singleton instance
email_queue_service = EmailQueueService()
