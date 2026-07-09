"""
Admin Dashboard Schemas
=======================
Defines validation and response schemas for system metrics, user/camera updates,
dynamic settings configurations, logs, and overall system status.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SystemStatusResponse(BaseModel):
    cpu_percent: float = Field(..., example=12.5)
    memory_percent: float = Field(..., example=45.2)
    memory_used_gb: float = Field(..., example=7.2)
    memory_total_gb: float = Field(..., example=16.0)
    disk_percent: float = Field(..., example=55.8)
    disk_used_gb: float = Field(..., example=220.5)
    disk_total_gb: float = Field(..., example=500.0)
    uptime_seconds: float = Field(..., example=86400.0)
    api_status: str = Field("healthy", example="healthy")


class UserUpdateSchema(BaseModel):
    role: Optional[str] = Field(None, description="User role: admin, officer, operator, viewer")
    status: Optional[str] = Field(None, description="User status: active, inactive")


class CameraUpdateSchema(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None  # online, offline
    health_status: Optional[str] = None  # good, warning, critical
    lat: Optional[float] = None
    lng: Optional[float] = None


class SMTPSettingsSchema(BaseModel):
    host: str = Field(..., example="smtp.gmail.com")
    port: int = Field(..., example=587)
    email: str = Field(..., example="test@gmail.com")
    password: Optional[str] = Field(None, example="xxxx xxxx xxxx xxxx")
    use_tls: bool = Field(True, example=True)
    sender: str = Field(..., example="Sender <test@gmail.com>")


class AISettingsSchema(BaseModel):
    confidence_threshold: float = Field(..., example=0.45)
    speed_limit_kmh: float = Field(..., example=60.0)
    enabled_modules: List[str] = Field(..., example=["helmet_detection", "ocr"])


class ConfigSettingsResponse(BaseModel):
    smtp: SMTPSettingsSchema
    ai: AISettingsSchema
    upload_dir: str = Field(..., example="data/uploads")


class ConfigSettingsUpdate(BaseModel):
    smtp: Optional[SMTPSettingsSchema] = None
    ai: Optional[AISettingsSchema] = None
    upload_dir: Optional[str] = None


class AIModuleStateSchema(BaseModel):
    name: str
    enabled: bool
    status: str  # Loaded, Disabled
    weights_status: str  # Pre-trained Weights Available, Not Trained, Rule-based


class OCRStatsSchema(BaseModel):
    requests_count: int
    verified_count: int
    rejected_count: int
    avg_confidence: float
    engine_name: str


class EmailStatsSchema(BaseModel):
    total_emails: int
    pending_emails: int
    sent_emails: int
    failed_emails: int


class StorageStatusResponse(BaseModel):
    total_size_mb: float
    files_count: int
    upload_dir: str


class DashboardSummaryResponse(BaseModel):
    total_vehicles: int
    total_violations: int
    total_cameras: int
    online_cameras: int
    total_users: int
    active_users: int
    system_status: SystemStatusResponse
    ocr_statistics: OCRStatsSchema
    email_statistics: EmailStatsSchema


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    timestamp: datetime
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class SystemLogsResponse(BaseModel):
    log_file: str
    total_lines: int
    lines: List[str]


class HealthStatusResponse(BaseModel):
    status: str  # ok, degraded, error
    database: bool
    system_resources: bool
    api_health: bool
