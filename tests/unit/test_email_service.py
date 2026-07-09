"""
Unit Tests for EmailService, EmailTemplateService, and EmailQueueService
========================================================================
Asserts:
  1. Config settings validation.
  2. SMTP connection lifecycle, authentication, and TLS mocking.
  3. HTML template rendering checks.
  4. Attachment existence checking.
  5. Queue processing transactions and state transitions (pending -> sent).
  6. Retry counts incrementation and terminal failure states (pending -> retrying -> failed).
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from backend.app.database import Base
from backend.app.config import settings
from backend.app.services.email_service import EmailService
from backend.app.services.email_template_service import email_template_service
from backend.app.services.email_queue_service import EmailQueueService
from backend.app.repositories.email_repository import EmailRepository

# Set up clean in-memory SQLite database for testing queue operations
test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_database():
    # Recreate tables in-memory for each test run
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def mock_smtp_credentials():
    with patch("backend.app.services.email_service.settings.SMTP_APP_PASSWORD", "mocked_password"), \
         patch("backend.app.services.email_service.settings.SMTP_EMAIL", "coderazze95@gmail.com"):
        from backend.app.services.email_service import email_service
        email_service.username = "coderazze95@gmail.com"
        email_service.password = "mocked_password"
        
        # Also patch queue service credentials
        from backend.app.services.email_queue_service import email_queue_service
        yield


def test_smtp_config_settings():
    assert settings.SMTP_HOST == "smtp.gmail.com"
    assert settings.SMTP_PORT == 587
    assert settings.SMTP_EMAIL == "coderazze95@gmail.com"
    assert settings.SMTP_USE_TLS is True


def test_template_rendering():
    context = {
        "plate": "MH12AB1234",
        "violation_type": "No Helmet",
        "timestamp": "2026-07-09 12:00:00",
        "location": "Sector 5 intersection",
        "confidence": 0.925,
        "evidence_id": "test-ev-uuid"
    }

    html, text = email_template_service.render("notice", context)
    assert "TRAFFIC VIOLATION NOTICE" in html
    assert "MH12AB1234" in html
    assert "No Helmet" in html
    assert "Sector 5 intersection" in html
    assert "92.50%" in html
    
    assert "=== OFFICIAL TRAFFIC VIOLATION NOTICE ===" in text
    assert "MH12AB1234" in text


@patch("smtplib.SMTP")
def test_smtp_client_lifecycle(mock_smtp_class):
    mock_smtp_inst = MagicMock()
    mock_smtp_class.return_value = mock_smtp_inst

    service = EmailService()
    service.username = "test@gmail.com"
    service.password = "secretpass"

    # Connect
    server = service.connect_smtp()
    assert server == mock_smtp_inst
    mock_smtp_inst.starttls.assert_called_once()
    mock_smtp_inst.login.assert_called_once_with("test@gmail.com", "secretpass")

    # Disconnect
    service.close_smtp(server)
    mock_smtp_inst.quit.assert_called_once()


def test_attachment_handling_missing_files():
    service = EmailService()
    # Test checking logic - should safely omit non-existent files without raising exceptions
    msg = service.create_mime_message(
        recipient="target@gmail.com",
        subject="Notice",
        html_body="<html></html>",
        text_body="plain text",
        attachments=["/nonexistent/crop1.jpg", "/nonexistent/crop2.jpg"]
    )
    # Check that it has only text and html subparts (multipart/alternative)
    # and no octet-stream attachments were added
    payload = msg.get_payload()
    assert len(payload) == 1  # only the multipart/alternative subpart


@patch("smtplib.SMTP")
def test_email_queue_lifecycle(mock_smtp_class):
    mock_smtp_inst = MagicMock()
    mock_smtp_class.return_value = mock_smtp_inst

    db = TestSessionLocal()
    queue_service = EmailQueueService()
    
    # 1. Queue an email notice
    context = {"plate": "DL3C4567", "violation_type": "Wrong Side"}
    queue_service.queue_email(
        db=db,
        recipient="violator@gmail.com",
        subject="Traffic Violation DL3C4567",
        template_name="notice",
        context_data=context
    )

    # Verify state is pending in database
    repo = EmailRepository(db)
    pending = repo.get_pending_queue(max_retries=3)
    assert len(pending) == 1
    assert pending[0].recipient == "violator@gmail.com"
    assert pending[0].status == "pending"

    # 2. Process queue successfully
    mock_smtp_inst.sendmail.return_value = {}
    sent_count = queue_service.process_queue(db)
    
    assert sent_count == 1
    
    # Verify status changed to sent
    db.expire_all()
    finished = repo.get_logs_by_recipient("violator@gmail.com")
    assert len(finished) == 1
    assert finished[0].status == "sent"
    assert finished[0].retry_count == 0

    db.close()


@patch("smtplib.SMTP")
def test_email_queue_failure_and_retry(mock_smtp_class):
    mock_smtp_inst = MagicMock()
    mock_smtp_class.return_value = mock_smtp_inst

    # Force connection or send error
    mock_smtp_inst.login.side_effect = Exception("Auth Failure")

    db = TestSessionLocal()
    queue_service = EmailQueueService()
    repo = EmailRepository(db)

    # Queue notice
    queue_service.queue_email(
        db=db,
        recipient="violator2@gmail.com",
        subject="Notice 2",
        template_name="notice",
        context_data={"plate": "MH12EE9999"}
    )

    # Process queue (will fail connection due to mocked login Auth Failure)
    sent_count = queue_service.process_queue(db)
    assert sent_count == 0

    # Assert retry status and retry count incremented
    db.expire_all()
    logs = repo.get_logs_by_recipient("violator2@gmail.com")
    assert len(logs) == 1
    assert logs[0].status == "retrying"
    assert logs[0].retry_count == 1
    assert "Auth Failure" in logs[0].error_message

    # Fail again on second run
    queue_service.process_queue(db)
    db.expire_all()
    assert repo.get_logs_by_recipient("violator2@gmail.com")[0].status == "retrying"
    assert repo.get_logs_by_recipient("violator2@gmail.com")[0].retry_count == 2

    # Fail third run (limit is 3 retries, so it should transition to failed)
    queue_service.process_queue(db)
    db.expire_all()
    assert repo.get_logs_by_recipient("violator2@gmail.com")[0].status == "failed"
    assert repo.get_logs_by_recipient("violator2@gmail.com")[0].retry_count == 3

    db.close()
