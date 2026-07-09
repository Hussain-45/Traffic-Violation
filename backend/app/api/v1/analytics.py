"""
Analytics FastAPI API Endpoints
==============================
Defines the REST endpoints for pulling dashboard summaries, metrics, and report exports.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.database import get_db
from backend.app.controllers.analytics_controller import analytics_controller
from backend.app.schemas.analytics_schema import DashboardSummaryResponse

router = APIRouter(prefix="/analytics", tags=["Analytics V1"])


@router.get("/dashboard", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    plate: Optional[str] = Query(None, description="License plate query filter"),
    violation_type: Optional[str] = Query(None, description="Violation category filter"),
    camera_id: Optional[str] = Query(None, description="Camera ID query filter"),
    status: Optional[str] = Query(None, description="Violation status filter"),
    db: Session = Depends(get_db)
):
    """Fetches consolidated dashboard KPIs, trends, offender lists, and stats."""
    filters = analytics_controller.parse_filters(
        start_date=start_date,
        end_date=end_date,
        plate=plate,
        violation_type=violation_type,
        camera_id=camera_id,
        status=status
    )
    return analytics_controller.get_dashboard_summary(db, filters)


@router.get("/statistics")
def get_statistics(db: Session = Depends(get_db)):
    """Returns general violation summary metrics."""
    summary = analytics_controller.get_dashboard_summary(db, {})
    return summary["kpis"]


@router.get("/trends")
def get_trends(
    interval: str = Query("day", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """Returns chronological violation and fine count trends."""
    summary = analytics_controller.get_dashboard_summary(db, {})
    if interval == "week":
        return summary["weekly_trends"]
    elif interval == "month":
        return summary["monthly_trends"]
    return summary["daily_trends"]


@router.get("/vehicles")
def get_vehicles_stats(db: Session = Depends(get_db)):
    """Returns vehicle category counts."""
    summary = analytics_controller.get_dashboard_summary(db, {})
    return summary["vehicle_distribution"]


@router.get("/violations")
def get_violations_stats(db: Session = Depends(get_db)):
    """Returns violation class counts."""
    summary = analytics_controller.get_dashboard_summary(db, {})
    return summary["violation_distribution"]


@router.get("/emails")
def get_emails_stats(db: Session = Depends(get_db)):
    """Returns email delivery statistics."""
    summary = analytics_controller.get_dashboard_summary(db, {})
    return summary["email_delivery_stats"]


@router.get("/evidence")
def get_evidence_stats(db: Session = Depends(get_db)):
    """Returns evidence package generation stats."""
    summary = analytics_controller.get_dashboard_summary(db, {})
    return {
        "total_evidence_recorded": summary["kpis"]["total_violations"],
        "rule_specific_confidence": summary["rule_specific_stats"]
    }


@router.get("/export")
def export_analytics(
    format: str = Query("csv", regex="^(csv|xlsx|pdf|json)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    violation_type: Optional[str] = Query(None),
    camera_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Generates and downloads filtered violation log files (CSV/Excel/PDF/JSON)."""
    filters = analytics_controller.parse_filters(
        start_date=start_date,
        end_date=end_date,
        violation_type=violation_type,
        camera_id=camera_id
    )
    try:
        content, media_type, filename = analytics_controller.get_export(db, filters, format)
        
        if format == "xlsx":
            return Response(
                content=content,
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/health")
def get_system_health(db: Session = Depends(get_db)):
    """Returns system performance diagnostics and database connectivity health."""
    summary = analytics_controller.get_dashboard_summary(db, {})
    return {
        "db_connection": summary["kpis"]["db_health"],
        "system_uptime": summary["kpis"]["system_uptime"],
        "performance_metrics": summary["performance_metrics"]
    }
