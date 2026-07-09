"""
Report Repository Layer
=======================
Handles database access and query mappings for report creation, lookups, and state updates.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from backend.app.models.report_model import Report


class ReportRepository:
    """
    Encapsulates database operations for report audit records.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, report_obj: Report) -> Report:
        """Persists a new report record in the database."""
        self.db.add(report_obj)
        self.db.commit()
        self.db.refresh(report_obj)
        return report_obj

    def get_by_id(self, report_id: int) -> Optional[Report]:
        """Looks up a report record by its primary key ID."""
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_all(self, filters: Dict[str, Any] = None) -> List[Report]:
        """Retrieves report history list with dynamic optional filters."""
        query = self.db.query(Report)
        
        if filters:
            clauses = []
            if filters.get("report_type"):
                clauses.append(Report.report_type == filters["report_type"])
            if filters.get("format"):
                clauses.append(Report.format == filters["format"])
            if filters.get("status"):
                clauses.append(Report.status == filters["status"])
            
            if clauses:
                query = query.filter(and_(*clauses))

        return query.order_by(desc(Report.created_at)).all()

    def update_status(self, report_id: int, status: str, file_path: str = None) -> Optional[Report]:
        """Updates the status and filepath of an existing report compilation."""
        report = self.get_by_id(report_id)
        if report:
            report.status = status
            if file_path:
                report.file_path = file_path
            self.db.commit()
            self.db.refresh(report)
        return report

    def delete(self, report_id: int) -> bool:
        """Deletes a report record from the database."""
        report = self.get_by_id(report_id)
        if report:
            self.db.delete(report)
            self.db.commit()
            return True
        return False
