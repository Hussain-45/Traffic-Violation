import io
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.app.database import get_db
from backend.app.models import Violation, Vehicle, Camera, User
from backend.app.auth.jwt import get_current_user
import pandas as pd

router = APIRouter(prefix="/analytics", tags=["Analytics"])

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

@router.get("/export")
def export_violations_report(
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch all violations
    violations = db.query(Violation).all()
    
    # Map to flat dictionary format
    data = []
    for v in violations:
        data.append({
            "Violation ID": v.id,
            "License Plate": v.vehicle.license_plate,
            "Vehicle Type": v.vehicle.type,
            "Vehicle Brand": v.vehicle.brand,
            "Owner Name": v.vehicle.owner_name,
            "Camera ID": v.camera_id,
            "Camera Location": v.location,
            "Violation Type": v.type.replace("_", " ").title(),
            "Timestamp": v.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Fine Amount (INR)": v.fine_amount,
            "Status": v.status.upper(),
            "Officer Notes": v.officer_notes or "N/A"
        })
        
    df = pd.DataFrame(data)
    
    if format == "csv":
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=traffic_violations_report.csv"
        return response
    else:
        # Excel format
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Violations")
        output.seek(0)
        response = StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = "attachment; filename=traffic_violations_report.xlsx"
        return response
