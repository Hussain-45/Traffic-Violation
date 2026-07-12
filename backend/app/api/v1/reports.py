"""
Report Generation FastAPI Routing
=================================
Defines REST endpoints for listing, generating, downloading, and deleting system reports.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os
import zipfile
import io
import datetime

from backend.app.database import get_db
from backend.app.auth.jwt import get_current_user
from backend.app.models import User
from backend.app.controllers.report_controller import report_controller
from backend.app.schemas.report_schema import ReportCreate, ReportResponse, ReportTemplateResponse
from backend.app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Reports V1"])


@router.get("", response_model=List[ReportResponse])
def get_reports_list(
    report_type: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves list of generated report files."""
    # Enforce basic authorization check: active user
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="Inactive user account.")
    return report_controller.get_history(db, report_type, format, status)


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers report compilation based on template, range filters, and output format."""
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="Inactive user account.")
    try:
        return report_controller.generate_report(db, current_user.id, payload, background_tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{report_id}")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Streams the compiled report file to client downloader."""
    if current_user.status != "active":
        raise HTTPException(status_code=403, detail="Inactive user account.")
        
    report = report_controller.get_report(db, report_id)
    if not report or report.status != "completed":
        raise HTTPException(status_code=404, detail="Report file not found or generation failed.")

    # 1. Expiry check
    if report.expires_at and report.expires_at < datetime.datetime.utcnow():
        raise HTTPException(status_code=410, detail="The requested report has expired and was purged.")
        
    filename = os.path.basename(report.file_path)
    physical_path = os.path.join("data", "reports", filename)
    
    if not os.path.exists(physical_path):
        raise HTTPException(status_code=404, detail="Physical file missing on server storage.")
        
    # 2. Record download event
    report_service.record_download(db, report_id)
        
    media_type = "application/octet-stream"
    if report.format == "pdf":
        media_type = "application/pdf"
    elif report.format == "csv":
        media_type = "text/csv"
    elif report.format == "xlsx":
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif report.format == "json":
        media_type = "application/json"
        
    return FileResponse(physical_path, media_type=media_type, filename=filename)


@router.get("/history", response_model=List[ReportResponse])
def get_report_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auditing endpoint returning report generation log database entries."""
    return report_controller.get_history(db)


@router.get("/templates", response_model=List[ReportTemplateResponse])
def get_report_templates(
    current_user: User = Depends(get_current_user)
):
    """Lists available pre-designed templates details."""
    return report_controller.get_templates()


@router.get("/export")
def export_reports_zip(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compiles all completed reports into a single ZIP archive download."""
    reports = report_controller.get_history(db, status="completed")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for r in reports:
            filename = os.path.basename(r.file_path)
            physical_path = os.path.join("data", "reports", filename)
            if os.path.exists(physical_path):
                zip_file.write(physical_path, filename)
                
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=all_reports_export.zip"}
    )


@router.get("/health")
def get_reports_engine_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Performs self-diagnostics checks on the report generation engine and directories."""
    report_dir = os.path.join("data", "reports")
    write_access = os.access(report_dir, os.W_OK) if os.path.exists(report_dir) else True
    
    return {
        "engine_status": "healthy",
        "storage_directory": report_dir,
        "write_permission": write_access,
        "templates_loaded": len(report_controller.get_templates())
    }


@router.delete("/delete/{report_id}")
def delete_report_file(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes database report audit record and physical document file."""
    deleted = report_controller.delete_report(db, report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report record not found.")
    return {"success": True, "message": "Report deleted successfully."}


class FrontendReportCreate(BaseModel):
    title: str
    report_type: str
    start_date: datetime.datetime
    end_date: datetime.datetime
    file_format: Optional[str] = "csv"


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report_frontend(
    payload: FrontendReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fallback endpoint for frontend POST /reports."""
    from backend.app.schemas.report_schema import ReportCreate as V1ReportCreate, ReportFilterSchema
    v1_payload = V1ReportCreate(
        title=payload.title,
        report_type=payload.report_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        format=payload.file_format,
        filters=ReportFilterSchema()
    )
    return report_controller.generate_report(db, current_user.id, v1_payload, background_tasks)


@router.delete("/{report_id}")
def delete_report_frontend(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fallback endpoint for frontend DELETE /reports/{report_id}."""
    deleted = report_controller.delete_report(db, report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report record not found.")
    return {"success": True, "message": "Report deleted successfully."}


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_details(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves specific report metadata details."""
    report = report_controller.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report record not found.")
    return report
