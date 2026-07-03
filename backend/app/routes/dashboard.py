import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.app.database import get_db
from backend.app.models import Violation, Vehicle, Camera, User, ActivityLog
from backend.app.auth.jwt import get_current_user
from typing import Dict, Any, List

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total counts
    total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0
    total_violations = db.query(func.count(Violation.id)).scalar() or 0
    
    # Today's counts
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_violations = db.query(func.count(Violation.id)).filter(
        Violation.timestamp >= today_start
    ).scalar() or 0
    
    # Financial Stats
    fines_collected = db.query(func.sum(Violation.fine_amount)).filter(
        Violation.status == "paid"
    ).scalar() or 0.0
    fines_pending = db.query(func.sum(Violation.fine_amount)).filter(
        Violation.status == "pending"
    ).scalar() or 0.0
    
    # Weekly Trends (Last 7 days)
    weekly_trends = []
    for i in range(6, -1, -1):
        day_date = datetime.datetime.utcnow() - datetime.timedelta(days=i)
        day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + datetime.timedelta(days=1)
        
        count = db.query(func.count(Violation.id)).filter(
            and_(Violation.timestamp >= day_start, Violation.timestamp < day_end)
        ).scalar() or 0
        
        weekly_trends.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "day": day_start.strftime("%a"),
            "count": count
        })
        
    # Violation Types Share
    type_distribution = db.query(
        Violation.type, func.count(Violation.id)
    ).group_by(Violation.type).all()
    
    type_data = [
        {"name": item[0].replace("_", " ").title(), "value": item[1]}
        for item in type_distribution
    ]
    
    # Recent Detections (top 6)
    recent_violations = db.query(Violation).order_by(
        Violation.timestamp.desc()
    ).limit(6).all()
    
    recent_list = []
    for v in recent_violations:
        recent_list.append({
            "id": v.id,
            "plate": v.vehicle.license_plate,
            "type": v.type.replace("_", " ").title(),
            "location": v.location,
            "timestamp": v.timestamp.isoformat(),
            "fine_amount": v.fine_amount,
            "status": v.status,
            "evidence_image": v.evidence_image_path
        })
        
    # Camera Status
    total_cameras = db.query(func.count(Camera.id)).scalar() or 0
    online_cameras = db.query(func.count(Camera.id)).filter(Camera.status == "online").scalar() or 0
    
    # Heatmap Locations (group by lat, lng)
    heatmap_query = db.query(
        Camera.lat, Camera.lng, Camera.location, func.count(Violation.id).label("weight")
    ).join(Violation, Camera.id == Violation.camera_id).group_by(Camera.id).all()
    
    heatmap_data = [
        {"lat": item.lat, "lng": item.lng, "name": item.location, "count": item.weight}
        for item in heatmap_query
    ]
    
    # Recent Officer Action Logs
    recent_logs = db.query(ActivityLog).order_by(
        ActivityLog.timestamp.desc()
    ).limit(5).all()
    
    log_list = []
    for l in recent_logs:
        log_list.append({
            "id": l.id,
            "username": l.user.username,
            "action": l.action,
            "timestamp": l.timestamp.isoformat()
        })

    return {
        "summary": {
            "total_vehicles": total_vehicles,
            "total_violations": total_violations,
            "today_violations": today_violations,
            "fines_collected": float(fines_collected),
            "fines_pending": float(fines_pending),
            "total_cameras": total_cameras,
            "online_cameras": online_cameras,
        },
        "weekly_trends": weekly_trends,
        "type_distribution": type_data,
        "recent_violations": recent_list,
        "heatmap": heatmap_data,
        "recent_logs": log_list
    }
