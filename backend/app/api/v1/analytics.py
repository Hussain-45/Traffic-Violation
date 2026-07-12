"""
Analytics FastAPI API Endpoints
==============================
Defines the REST endpoints for pulling dashboard summaries, metrics, and report exports.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import Optional
import datetime
from sqlalchemy import func, and_

from backend.app.database import get_db
from backend.app.controllers.analytics_controller import analytics_controller
from backend.app.schemas.analytics_schema import DashboardSummaryResponse
from backend.app.models import Violation, Vehicle, Camera, User
from backend.app.auth.jwt import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics V1"])

@router.get("/charts")
def get_analytics_charts(
    time_span: str | None = None,
    camera_id: str | None = None,
    officer_id: int | None = None,
    violation_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Build dynamic filter predicates list
    filters = []
    
    if time_span == "today":
        start_time = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        filters.append(Violation.timestamp >= start_time)
    elif time_span == "last_7_days":
        start_time = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        filters.append(Violation.timestamp >= start_time)
    elif time_span == "last_month":
        start_time = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        filters.append(Violation.timestamp >= start_time)
        
    if camera_id and camera_id != "all":
        filters.append(Violation.camera_id == camera_id)
        
    if violation_type and violation_type != "all":
        filters.append(Violation.type == violation_type)

    violation_filter = and_(*filters) if filters else True

    # 1. Violation Categories (detailed counts and sum of fines)
    categories_query = db.query(
        Violation.type,
        func.count(Violation.id).label("count"),
        func.sum(Violation.fine_amount).label("total_fines")
    ).filter(violation_filter).group_by(Violation.type).all()
    
    categories = []
    for item in categories_query:
        categories.append({
            "type": item.type.replace("_", " ").title(),
            "count": item.count,
            "total_fines": float(item.total_fines or 0.0)
        })
        
    # 2. Vehicle Types count
    vehicle_types_query = db.query(
        Vehicle.type,
        func.count(Violation.id).label("count")
    ).join(Violation, Vehicle.id == Violation.vehicle_id).filter(violation_filter).group_by(Vehicle.type).all()
    
    vehicle_types = []
    for item in vehicle_types_query:
        vehicle_types.append({
            "name": item.type.capitalize(),
            "value": item.count
        })
        
    # 3. Peak traffic/violation hours (0-23 hours distribution)
    hourly_query = db.query(
        Violation.timestamp
    ).filter(violation_filter).all()
    
    hourly_counts = [0] * 24
    for item in hourly_query:
        hour = item.timestamp.hour
        hourly_counts[hour] += 1
        
    hourly_data = [
        {"hour": f"{hour:02d}:00", "violations": count}
        for hour, count in enumerate(hourly_counts)
    ]
    
    # 4. Monthly Violations (last 6 months)
    monthly_data = []
    current_date = datetime.datetime.utcnow()
    for i in range(5, -1, -1):
        target_date = current_date - datetime.timedelta(days=i*30)
        start_date = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = start_date + datetime.timedelta(days=32)
        end_date = next_month.replace(day=1)
        
        count = db.query(func.count(Violation.id)).filter(
            and_(Violation.timestamp >= start_date, Violation.timestamp < end_date),
            violation_filter
        ).scalar() or 0
        
        fines = db.query(func.sum(Violation.fine_amount)).filter(
            and_(Violation.timestamp >= start_date, Violation.timestamp < end_date),
            violation_filter
        ).scalar() or 0.0
        
        monthly_data.append({
            "month": start_date.strftime("%b"),
            "violations": count,
            "fines": float(fines)
        })
        
    # 5. Detection Accuracy (confidence score buckets)
    mean_conf = db.query(func.avg(Violation.confidence_score)).filter(violation_filter).scalar() or 0.92
    
    return {
        "categories": categories,
        "vehicle_types": vehicle_types,
        "hourly_trends": hourly_data,
        "monthly_trends": monthly_data,
        "detection_accuracy": round(float(mean_conf) * 100, 1)
    }


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
