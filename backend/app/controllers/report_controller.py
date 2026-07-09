"""
Report Controller Layer
=======================
Coordinates parameter parsing and triggers ReportService generation.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.services.report_service import report_service
from backend.app.schemas.report_schema import ReportCreate
from backend.app.models.report_model import Report


class ReportController:
    """
    Decouples FastAPI HTTP routing from the core ReportService business logic.
    """

    def generate_report(self, db: Session, user_id: int, payload: ReportCreate) -> Report:
        """Parses inputs and triggers file compilation."""
        return report_service.generate_report(db, user_id, payload)

    def get_report(self, db: Session, report_id: int) -> Optional[Report]:
        """Retrieves a single report details by ID."""
        return report_service.get_report(db, report_id)

    def get_history(self, db: Session, report_type: Optional[str] = None, format: Optional[str] = None, status: Optional[str] = None) -> List[Report]:
        """Gathers previous report records filtered by type, format, or status."""
        filters = {}
        if report_type:
            filters["report_type"] = report_type
        if format:
            filters["format"] = format
        if status:
            filters["status"] = status
        return report_service.get_history(db, filters)

    def get_templates(self) -> List[Dict[str, Any]]:
        """Lists metadata details for supported templates."""
        return report_service.get_templates()

    def delete_report(self, db: Session, report_id: int) -> bool:
        """Deletes database record and its associated physical file."""
        return report_service.delete_report(db, report_id)


# Singleton controller instance
report_controller = ReportController()
