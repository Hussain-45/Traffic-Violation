"""
Analytics Repository Layer
==========================
Executes database aggregation queries for KPIs, trends, class distributions, and offenders.
"""
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
import datetime

from backend.app.models import Violation, Vehicle, Camera
from backend.app.models.evidence_model import EvidenceModel
from backend.app.models.email_log_model import EmailLogModel
from backend.app.models.analytics_model import AnalyticsReportModel
from backend.app.schemas.analytics_schema import AnalyticsReportCreate


class AnalyticsRepository:
    """
    Encapsulates database aggregation queries for analytics and dashboard views.
    """

    def __init__(self, db: Session):
        self.db = db

    def _build_filter_clauses(self, filters: Dict[str, Any]) -> List[Any]:
        """Builds dynamic filter conditions based on request parameters."""
        clauses = []
        
        # Date range filtering
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            clauses.append(Violation.timestamp >= start_date)
        if end_date:
            clauses.append(Violation.timestamp <= end_date)

        # Plate number filtering
        plate = filters.get("plate")
        if plate:
            clauses.append(Vehicle.license_plate.like(f"%{plate}%"))

        # Violation type filtering
        violation_type = filters.get("violation_type")
        if violation_type:
            clauses.append(Violation.type == violation_type)

        # Camera ID filtering
        camera_id = filters.get("camera_id")
        if camera_id:
            clauses.append(Violation.camera_id == camera_id)

        # Status filtering
        status = filters.get("status")
        if status:
            clauses.append(Violation.status == status)

        return clauses

    def get_kpis(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Computes totals and average confidence from database tables."""
        clauses = self._build_filter_clauses(filters)
        filter_clause = and_(*clauses) if clauses else True

        # Total violations
        total_violations = self.db.query(func.count(Violation.id)).filter(filter_clause).scalar() or 0

        # Total vehicles
        total_vehicles = self.db.query(func.count(Vehicle.id)).scalar() or 0

        # Active cameras
        active_cameras = self.db.query(func.count(Camera.id)).filter(Camera.status == "online").scalar() or 0

        # Total fine amount
        total_fines = self.db.query(func.sum(Violation.fine_amount)).filter(filter_clause).scalar() or 0.0

        # Average confidence
        avg_confidence = self.db.query(func.avg(Violation.confidence_score)).filter(filter_clause).scalar() or 0.0

        return {
            "total_violations": total_violations,
            "total_vehicles": total_vehicles,
            "active_cameras": active_cameras,
            "total_fines": float(total_fines),
            "avg_confidence": float(avg_confidence)
        }

    def get_trends(self, interval: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Groups violations by date parts (day, week, month).
        Supports both SQLite and PostgreSQL engines dynamically.
        """
        clauses = self._build_filter_clauses(filters)
        filter_clause = and_(*clauses) if clauses else True

        is_sqlite = self.db.bind.dialect.name == "sqlite"

        # Determine date-formatting expression dynamically
        if interval == "day":
            date_expr = func.strftime("%Y-%m-%d", Violation.timestamp) if is_sqlite else func.to_char(Violation.timestamp, "YYYY-MM-DD")
        elif interval == "week":
            date_expr = func.strftime("%Y-W%W", Violation.timestamp) if is_sqlite else func.to_char(Violation.timestamp, "YYYY-W\"IW\"")
        elif interval == "month":
            date_expr = func.strftime("%Y-%m", Violation.timestamp) if is_sqlite else func.to_char(Violation.timestamp, "YYYY-MM")
        else:
            date_expr = func.strftime("%Y-%m-%d", Violation.timestamp) if is_sqlite else func.to_char(Violation.timestamp, "YYYY-MM-DD")

        query_results = self.db.query(
            date_expr.label("period"),
            func.count(Violation.id).label("count"),
            func.sum(Violation.fine_amount).label("fines")
        ).filter(filter_clause).group_by("period").order_by("period").all()

        trends = []
        for r in query_results:
            trends.append({
                "date": r.period,
                "count": r.count,
                "fines": float(r.fines or 0.0)
            })
        return trends

    def get_violation_distribution(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Groups violations by type."""
        clauses = self._build_filter_clauses(filters)
        filter_clause = and_(*clauses) if clauses else True

        results = self.db.query(
            Violation.type,
            func.count(Violation.id).label("count")
        ).filter(filter_clause).group_by(Violation.type).order_by(desc("count")).all()

        return [{"name": r.type.replace("_", " ").title(), "value": r.count} for r in results]

    def get_vehicle_distribution(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Groups vehicles by class type."""
        results = self.db.query(
            Vehicle.type,
            func.count(Vehicle.id).label("count")
        ).group_by(Vehicle.type).order_by(desc("count")).all()

        return [{"name": r.type.capitalize(), "value": r.count} for r in results]

    def get_top_offenders(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Identifies plates with repeated violations."""
        results = self.db.query(
            Vehicle.license_plate,
            func.count(Violation.id).label("count")
        ).join(Violation, Vehicle.id == Violation.vehicle_id).group_by(Vehicle.license_plate).order_by(desc("count")).limit(limit).all()

        return [{"plate": r.license_plate, "violation_count": r.count} for r in results]

    def get_top_cameras(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Identifies cameras with the highest violation log counts."""
        results = self.db.query(
            Violation.camera_id,
            Camera.location.label("location"),
            func.count(Violation.id).label("count")
        ).join(Camera, Violation.camera_id == Camera.id).group_by(Violation.camera_id, Camera.location).order_by(desc("count")).limit(limit).all()

        return [{"camera_id": r.camera_id, "location": r.location, "violation_count": r.count} for r in results]

    def get_email_statistics(self) -> Dict[str, int]:
        """Groups email log entries by status."""
        results = self.db.query(
            EmailLogModel.status,
            func.count(EmailLogModel.id)
        ).group_by(EmailLogModel.status).all()

        stats = {"pending": 0, "sending": 0, "sent": 0, "failed": 0, "retrying": 0}
        for status, count in results:
            if status in stats:
                stats[status] = count
        return stats

    def get_rule_specific_stats(self, filters: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Calculates violation counts and average confidence per rule."""
        clauses = self._build_filter_clauses(filters)
        filter_clause = and_(*clauses) if clauses else True

        results = self.db.query(
            Violation.type,
            func.count(Violation.id).label("count"),
            func.avg(Violation.confidence_score).label("avg_conf")
        ).filter(filter_clause).group_by(Violation.type).all()

        stats = {}
        for type_name, count, avg_conf in results:
            stats[type_name] = {
                "count": count,
                "avg_confidence": float(avg_conf or 0.0)
            }
        return stats

    def get_heatmap_coordinates(self) -> List[Dict[str, Any]]:
        """Returns coordinate mapping fields for active cameras."""
        results = self.db.query(
            Camera.lat,
            Camera.lng,
            Camera.location,
            func.count(Violation.id).label("count")
        ).join(Violation, Camera.id == Violation.camera_id).group_by(Camera.lat, Camera.lng, Camera.location).all()

        return [{
            "lat": r.lat,
            "lng": r.lng,
            "location": r.location,
            "weight": r.count
        } for r in results]

    def create_report_snapshot(self, schema: AnalyticsReportCreate) -> AnalyticsReportModel:
        """Saves a report snapshot to the database."""
        db_obj = AnalyticsReportModel(
            report_name=schema.report_name,
            report_type=schema.report_type,
            start_date=schema.start_date,
            end_date=schema.end_date,
            summary_data=schema.summary_data
        )
        self.db.add(db_obj)
        self.db.flush()
        return db_obj
