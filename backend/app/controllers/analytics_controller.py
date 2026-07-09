"""
Analytics Controller
====================
Mediates HTTP parameter formats, filters validation, and business logic mapping.
"""
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
import datetime

from backend.app.services.analytics_service import analytics_service


class AnalyticsController:
    """
    Controller mediating requests from FastAPI routes to the underlying services.
    """

    def parse_filters(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        plate: Optional[str] = None,
        violation_type: Optional[str] = None,
        camera_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validates and maps query string parameters to typed values."""
        filters = {}
        
        # Parse start_date
        if start_date:
            try:
                filters["start_date"] = datetime.datetime.fromisoformat(start_date)
            except ValueError:
                pass
                
        # Parse end_date
        if end_date:
            try:
                filters["end_date"] = datetime.datetime.fromisoformat(end_date)
            except ValueError:
                pass

        if plate:
            filters["plate"] = plate
        if violation_type and violation_type != "all":
            filters["violation_type"] = violation_type
        if camera_id and camera_id != "all":
            filters["camera_id"] = camera_id
        if status:
            filters["status"] = status

        return filters

    def get_dashboard_summary(self, db: Session, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches the dashboard analytics summary."""
        return analytics_service.get_dashboard_summary(db, filters)

    def get_export(self, db: Session, filters: Dict[str, Any], format: str) -> Tuple[Any, str, str]:
        """Triggers data formatting and file streaming compiled objects."""
        return analytics_service.generate_export(db, filters, format)


# Singleton instance
from typing import Optional
analytics_controller = AnalyticsController()
