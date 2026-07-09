"""
Admin API Endpoints
====================
Exposes system diagnostic summaries, active module listings, user permissioning,
and dynamic settings configurations to authenticated administrators.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth.jwt import get_current_user, check_admin_role
from backend.app.models import User
from backend.app.schemas.admin_schema import (
    DashboardSummaryResponse,
    SystemStatusResponse,
    ConfigSettingsResponse,
    ConfigSettingsUpdate,
    StorageStatusResponse,
    SystemLogsResponse,
    AuditLogResponse,
    HealthStatusResponse,
    UserUpdateSchema,
    CameraUpdateSchema
)
from backend.app.controllers.admin_controller import admin_controller

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    """
    Retrieves system summary cards, camera status ratios, user states, and OCR metrics.
    """
    return admin_controller.get_dashboard_summary(db)


@router.get("/system", response_model=SystemStatusResponse)
def get_system_status(
    admin: User = Depends(check_admin_role)
):
    """
    Fetches real-time system performance statistics (CPU, RAM, Disk, Uptime).
    """
    return admin_controller.get_system_status()


@router.get("/cameras")
def list_cameras(
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    """
    Retrieves registered camera channels and active MJPEG connection streams.
    """
    return admin_controller.list_cameras(db)


@router.post("/cameras/{camera_id}/toggle")
def toggle_camera(
    camera_id: str,
    payload: Dict[str, bool],
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    """
    Enables or disables camera streaming nodes.
    """
    enabled = payload.get("enabled", True)
    success = admin_controller.toggle_camera(db, camera_id, enabled, admin.id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera channel not registered.")
    return {"status": "success", "message": f"Camera status updated to {'online' if enabled else 'offline'}."}


@router.post("/cameras/{camera_id}/restart")
def restart_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    """
    Restarts camera feed stream.
    """
    success = admin_controller.restart_camera(db, camera_id, admin.id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera node not found.")
    return {"status": "success", "message": "Camera restart sequence initiated."}


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    """
    Lists users along with roles and last active activities.
    """
    return admin_controller.list_users(db)


@router.put("/users/{user_id}")
def update_user_status(
    user_id: int,
    payload: UserUpdateSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    """
    Modifies permission roles and access statuses of a user.
    """
    success = admin_controller.update_user_status(
        db, user_id, payload.role, payload.status, admin.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="User record not found.")
    return {"status": "success", "message": "User settings updated."}


@router.get("/settings", response_model=ConfigSettingsResponse)
def get_settings(
    admin: User = Depends(check_admin_role)
):
    """
    Retrieves system configurations (SMTP, AI pipelines, upload directories).
    """
    return admin_controller.get_settings()


@router.put("/settings")
def update_settings(
    payload: ConfigSettingsUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    """
    Updates system settings dynamically and persists them to configuration files.
    """
    success = admin_controller.update_settings(payload.model_dump(exclude_none=True), admin.id, db)
    return {"status": "success", "message": "Configurations saved successfully."}


@router.get("/modules")
def list_modules(
    admin: User = Depends(check_admin_role)
):
    """
    Checks activation toggles and model availability for pipeline modules.
    """
    return admin_controller.list_modules()


@router.get("/logs", response_model=SystemLogsResponse)
def get_recent_logs(
    lines: int = Query(100, ge=1, le=1000),
    admin: User = Depends(check_admin_role)
):
    """
    Reads recent log entries from the system logger output.
    """
    return admin_controller.get_recent_logs(lines)


@router.get("/audit", response_model=List[AuditLogResponse])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    """
    Exposes chronological administrative audit trail history.
    """
    return admin_controller.list_audit_logs(db, page, page_size)


@router.get("/storage", response_model=StorageStatusResponse)
def get_storage_status(
    admin: User = Depends(check_admin_role)
):
    """
    Calculates total capacity utilized by visual evidence storage directories.
    """
    return admin_controller.get_storage_status()


@router.get("/health", response_model=HealthStatusResponse)
def get_health_status(
    admin: User = Depends(check_admin_role)
):
    """
    Aggregates checks for database connectivity and resource levels.
    """
    return admin_controller.get_health_status()
