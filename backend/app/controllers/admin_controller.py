"""
Admin Controller
================
Mediates HTTP routes to admin services and handles standard response formatting.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.services.admin_service import admin_service


class AdminController:
    """
    Mediator between FastAPI router endpoints and the AdminService business layer.
    """

    def get_dashboard_summary(self, db: Session) -> Dict[str, Any]:
        return admin_service.get_dashboard_summary(db)

    def get_system_status(self) -> Dict[str, Any]:
        return admin_service.get_system_status()

    def list_cameras(self, db: Session) -> List[Dict[str, Any]]:
        return admin_service.list_cameras(db)

    def toggle_camera(self, db: Session, camera_id: str, enabled: bool, admin_id: int) -> bool:
        return admin_service.toggle_camera(db, camera_id, enabled, admin_id)

    def restart_camera(self, db: Session, camera_id: str, admin_id: int) -> bool:
        return admin_service.restart_camera(db, camera_id, admin_id)

    def list_users(self, db: Session) -> List[Dict[str, Any]]:
        return admin_service.list_users(db)

    def update_user_status(self, db: Session, user_id: int, role: Optional[str], status: Optional[str], admin_id: int) -> bool:
        return admin_service.update_user_status(db, user_id, role, status, admin_id)

    def get_settings(self) -> Dict[str, Any]:
        return admin_service.get_settings()

    def update_settings(self, payload: Dict[str, Any], admin_id: int, db: Session) -> bool:
        return admin_service.update_settings(payload, admin_id, db)

    def list_modules(self) -> List[Dict[str, Any]]:
        return admin_service.list_modules()

    def get_storage_status(self) -> Dict[str, Any]:
        return admin_service.get_storage_status()

    def get_recent_logs(self, lines: int) -> Dict[str, Any]:
        return admin_service.get_recent_logs(lines)

    def list_audit_logs(self, db: Session, page: int, page_size: int) -> List[Dict[str, Any]]:
        return admin_service.list_audit_logs(db, page, page_size)

    def get_health_status(self) -> Dict[str, Any]:
        return admin_service.get_health_status()


# Singleton controller instance
admin_controller = AdminController()
