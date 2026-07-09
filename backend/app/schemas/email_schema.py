"""
Email Pydantic Schemas
======================
Defines input validation and output serialization schemas for email logs and queue send tasks.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EmailLogBase(BaseModel):
    evidence_id: Optional[str] = None
    violation_id: Optional[str] = None
    recipient: str
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    status: str = "pending"
    retry_count: int = 0
    error_message: Optional[str] = None


class EmailLogCreate(EmailLogBase):
    pass


class EmailLogUpdate(BaseModel):
    status: Optional[str] = None
    retry_count: Optional[int] = None
    error_message: Optional[str] = None


class EmailLogResponse(EmailLogBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class EmailSendRequest(BaseModel):
    recipient: str
    subject: str
    template_name: str  # notice, test, notification, failure
    context_data: Dict[str, Any] = Field(default_factory=dict)
