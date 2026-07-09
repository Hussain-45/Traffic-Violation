"""
Email Log SQLAlchemy ORM Model
==============================
Defines the database schema and status codes for email delivery tracking and auditing.
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from backend.app.database import Base


class EmailLogModel(Base):
    """
    SQLAlchemy model representing the 'email_logs' database table.
    Tracks state machine: pending -> sending -> sent / failed / retrying.
    """
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String, index=True, nullable=True)
    violation_id = Column(String, index=True, nullable=True)
    recipient = Column(String, index=True, nullable=False)
    subject = Column(String, nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    
    # Status codes: pending, sending, sent, failed, retrying
    status = Column(String, default="pending", index=True, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
