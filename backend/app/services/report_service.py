"""
Report Service Layer
===================
Consumes AnalyticsService data, coordinates templates, compiles output files,
and manages report audit log states.
"""
import os
import datetime
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.report_model import Report
from backend.app.schemas.report_schema import ReportCreate
from backend.app.repositories.report_repository import ReportRepository
from backend.app.services.analytics_service import analytics_service
from backend.app.services.report_template_service import report_template_service
from backend.app.config import settings


class ReportService:
    """
    Core service coordinating template styling, export formats, and database history.
    """

    def generate_report(self, db: Session, user_id: int, payload: ReportCreate) -> Report:
        """
        Gathers analytics metrics, renders template, writes file, and saves DB audit log.
        """
        repo = ReportRepository(db)

        # 1. Create directory
        report_dir = os.path.join(settings.UPLOAD_DIR, "reports") if hasattr(settings, "UPLOAD_DIR") else os.path.join("data", "reports")
        os.makedirs(report_dir, exist_ok=True)

        # 2. Instantiate pending DB record
        timestamp_str = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"report_{payload.report_type}_{timestamp_str}.{payload.format}"
        file_path = f"/data/reports/{filename}"

        db_report = Report(
            title=payload.title,
            generated_by=user_id,
            report_type=payload.report_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            file_path=file_path,
            status="generating",
            format=payload.format,
            filters=payload.filters.dict() if payload.filters else None
        )
        repo.create(db_report)

        # 3. Pull metrics and generate file
        try:
            filters = payload.filters.dict() if payload.filters else {}
            # Map start_date/end_date to filters to restrict query
            filters["start_date"] = payload.start_date
            filters["end_date"] = payload.end_date

            # Fetch analytics summary from AnalyticsService
            summary = analytics_service.get_dashboard_summary(db, filters)

            physical_file_path = os.path.join("data", "reports", filename)

            if payload.format == "pdf":
                # Compile PDF using text templates
                content = []
                content.append(report_template_service.render_cover_page(
                    title=payload.title,
                    report_type=payload.report_type,
                    start=payload.start_date.strftime("%Y-%m-%d"),
                    end=payload.end_date.strftime("%Y-%m-%d")
                ))
                content.append(report_template_service.render_kpis_table(summary["kpis"]))
                content.append(report_template_service.render_distributions(
                    summary["violation_distribution"],
                    summary["vehicle_distribution"]
                ))
                content.append(report_template_service.render_footer(1))

                with open(physical_file_path, "w", encoding="utf-8") as f:
                    f.write("".join(content))

            elif payload.format in ["csv", "xlsx", "json"]:
                # Delegate format compilation to AnalyticsService export engine
                stream_data, _, _ = analytics_service.generate_export(db, filters, payload.format)
                
                mode = "wb" if payload.format == "xlsx" else "w"
                encoding = None if payload.format == "xlsx" else "utf-8"
                
                with open(physical_file_path, mode, encoding=encoding) as f:
                    f.write(stream_data)

            else:
                raise ValueError(f"Unsupported format: {payload.format}")

            # 4. Mark completed
            repo.update_status(db_report.id, "completed", file_path)

        except Exception as e:
            # 5. Mark failed on error
            repo.update_status(db_report.id, "failed")
            raise RuntimeError(f"Report compilation failed: {e}")

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

    def delete_report(self, db: Session, report_id: int) -> bool:
        """Deletes a report record and its physical file if present."""
        repo = ReportRepository(db)
        report = repo.get_by_id(report_id)
        if report:
            # Try to delete physical file
            filename = os.path.basename(report.file_path)
            physical_file_path = os.path.join("data", "reports", filename)
            if os.path.exists(physical_file_path):
                try:
                    os.remove(physical_file_path)
                except Exception:
                    pass
            return repo.delete(report_id)
        return False


# Singleton service instance
report_service = ReportService()
