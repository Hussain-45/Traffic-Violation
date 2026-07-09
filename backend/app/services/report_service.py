"""
Report Service Layer
===================
Coordinates background asynchronous report generation, storage adapters,
version audits, and cryptographic checksum checks.
"""
import os
import datetime
import hashlib
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from backend.app.models.report_model import Report
from backend.app.schemas.report_schema import ReportCreate
from backend.app.repositories.report_repository import ReportRepository
from backend.app.services.analytics_service import analytics_service
from backend.app.services.report_template_service import report_template_service
from backend.app.services.report_context import ReportContext
from backend.app.services.export_service import export_service
from backend.app.services.storage_service import storage_service, StorageAdapter


class ReportService:
    """
    Orchestrates ReportContext assembly, ExportService conversion, and StorageAdapter persistency.
    Supports asynchronous generation via BackgroundTasks.
    """

    def __init__(self, storage: StorageAdapter = storage_service, session_maker: Any = None):
        self.storage = storage
        self.session_maker = session_maker

    def create_pending_report(self, db: Session, user_id: int, payload: ReportCreate) -> Report:
        """Saves a pending report log entry in the DB immediately."""
        repo = ReportRepository(db)
        
        timestamp_str = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"report_{payload.report_type}_{timestamp_str}.{payload.format}"
        file_path = f"/data/reports/{filename}"

        # Default 7-day retention expiry
        expiry = datetime.datetime.utcnow() + datetime.timedelta(days=7)

        db_report = Report(
            title=payload.title,
            generated_by=user_id,
            report_type=payload.report_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            file_path=file_path,
            status="generating",
            format=payload.format,
            version="1.0.0",
            filters=payload.filters.dict() if payload.filters else None,
            expires_at=expiry
        )
        return repo.create(db_report)

    def process_report_async(self, db_report_id: int, user_id: int, payload_dict: Dict[str, Any], db: Optional[Session] = None) -> None:
        """
        Background task compiling metrics, calculating checksum, and persisting to storage.
        Designed to be run in a separate background execution context.
        """
        close_session = False
        if db is None:
            if self.session_maker:
                db = self.session_maker()
            else:
                from backend.app.database import SessionLocal
                db = SessionLocal()
            close_session = True
            
        try:
            repo = ReportRepository(db)
            db_report = repo.get_by_id(db_report_id)
            if not db_report:
                return

            # Assemble query filters
            filters = payload_dict.get("filters") or {}
            filters["start_date"] = datetime.datetime.fromisoformat(payload_dict["start_date"]) if isinstance(payload_dict["start_date"], str) else payload_dict["start_date"]
            filters["end_date"] = datetime.datetime.fromisoformat(payload_dict["end_date"]) if isinstance(payload_dict["end_date"], str) else payload_dict["end_date"]

            # 1. Query AnalyticsService
            summary = analytics_service.get_dashboard_summary(db, filters)

            # 2. Build ReportContext
            context = ReportContext(
                report_id=db_report.id,
                generated_by=user_id,
                report_type=db_report.report_type,
                start_date=db_report.start_date,
                end_date=db_report.end_date,
                filters_applied=filters,
                kpis=summary["kpis"],
                violation_distribution=summary["violation_distribution"],
                vehicle_distribution=summary["vehicle_distribution"],
                version=db_report.version
            )

            # 3. Formulate output bytes
            raw_bytes = export_service.compile(context, db_report.format)

            # 4. Cryptographic checksum calculation
            checksum = hashlib.sha256(raw_bytes).hexdigest()
            db_report.checksum = checksum
            
            # Re-compile to include checksum in header (for PDF format)
            if db_report.format == "pdf":
                context.checksum = checksum
                raw_bytes = export_service.compile(context, db_report.format)

            # 5. Persist to storage using swappable StorageAdapter
            self.storage.save(db_report.file_path, raw_bytes)

            # 6. Update database status
            repo.update_status(db_report.id, "completed")

        except Exception as e:
            try:
                repo.update_status(db_report_id, "failed")
            except Exception:
                pass
            raise RuntimeError(f"Asynchronous report generation failed: {e}")
        finally:
            if close_session:
                db.close()

    def generate_report(self, db: Session, user_id: int, payload: ReportCreate, background_tasks: BackgroundTasks) -> Report:
        """
        Main entrypoint. Saves pending record immediately, schedules background task,
        and returns details to prevent blocking HTTP client threads.
        """
        # Save placeholder record
        db_report = self.create_pending_report(db, user_id, payload)
        
        # Serialize payload data for safe thread passing
        payload_dict = {
            "start_date": payload.start_date.isoformat(),
            "end_date": payload.end_date.isoformat(),
            "filters": payload.filters.dict() if payload.filters else {}
        }

        # Schedule async compilation
        background_tasks.add_task(
            self.process_report_async,
            db_report.id,
            user_id,
            payload_dict
        )

        return db_report

    def get_report(self, db: Session, report_id: int) -> Optional[Report]:
        """Looks up a report record."""
        return ReportRepository(db).get_by_id(report_id)

    def get_history(self, db: Session, filters: Dict[str, Any] = None) -> List[Report]:
        """Retrieves history logs list."""
        return ReportRepository(db).get_all(filters)

    def get_templates(self) -> List[Dict[str, Any]]:
        """Returns the list of supported templates."""
        return report_template_service.get_available_templates()

    def record_download(self, db: Session, report_id: int) -> Optional[Report]:
        """Records download access events in audit logs."""
        repo = ReportRepository(db)
        report = repo.get_by_id(report_id)
        if report:
            report.download_count = (report.download_count or 0) + 1
            db.commit()
            db.refresh(report)
        return report

    def delete_report(self, db: Session, report_id: int) -> bool:
        """Deletes a report record and its associated physical file."""
        repo = ReportRepository(db)
        report = repo.get_by_id(report_id)
        if report:
            self.storage.delete(report.file_path)
            return repo.delete(report_id)
        return False


# Singleton service instance
report_service = ReportService()
