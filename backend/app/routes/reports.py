from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Report, User, Violation, ActivityLog
from backend.app.auth.jwt import get_current_user
from pydantic import BaseModel
from typing import List, Optional
import datetime
import os
import csv

router = APIRouter(prefix="/reports", tags=["Reports"])

class ReportCreate(BaseModel):
    title: str
    report_type: str  # violations, revenue, analytics
    start_date: datetime.datetime
    end_date: datetime.datetime

class ReportOut(BaseModel):
    id: int
    title: str
    generated_by: int
    report_type: str
    start_date: datetime.datetime
    end_date: datetime.datetime
    file_path: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[ReportOut])
def get_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Report).all()

@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rep = db.query(Report).filter(Report.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report log not found")
    return rep

@router.post("", response_model=ReportOut)
def generate_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure directory exists
    report_dir = os.path.join("data", "reports")
    os.makedirs(report_dir, exist_ok=True)

    # Fetch violations within date range
    violations = db.query(Violation).filter(
        Violation.timestamp >= payload.start_date,
        Violation.timestamp <= payload.end_date
    ).all()

    # Generate filename
    timestamp_str = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"report_{payload.report_type}_{timestamp_str}.csv"
    file_path = os.path.join(report_dir, filename)

    try:
        # Write to CSV
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Violation ID", "Vehicle ID", "Camera ID", "Type", "Timestamp", "Location", "Fine", "Status", "Confidence"])
            for v in violations:
                writer.writerow([
                    v.id, v.vehicle_id, v.camera_id, v.type,
                    v.timestamp.isoformat(), v.location, v.fine_amount,
                    v.status, v.confidence_score
                ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report file: {e}")

    # Save to db
    # In FastAPI, we can expose the reports statically via app.mount("/data")
    static_url = f"/data/reports/{filename}"

    rep = Report(
        title=payload.title,
        generated_by=current_user.id,
        report_type=payload.report_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        file_path=static_url
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)

    # Log action
    log = ActivityLog(
        user_id=current_user.id,
        action=f"Generated '{payload.report_type}' report: '{payload.title}'"
    )
    db.add(log)
    db.commit()

    return rep

@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rep = db.query(Report).filter(Report.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")

    # Optional: Delete file
    # We clean up file path if it exists locally
    local_path = rep.file_path.lstrip("/")
    if os.path.exists(local_path):
        try:
            os.remove(local_path)
        except OSError:
            pass

    title = rep.title
    db.delete(rep)
    db.commit()

    # Log action
    log = ActivityLog(
        user_id=current_user.id,
        action=f"Deleted report log: '{title}'"
    )
    db.add(log)
    db.commit()

    return {"success": True, "message": f"Deleted report log for '{title}'."}
