from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Location, User, ActivityLog
from backend.app.auth.jwt import get_current_user, check_admin_role
from pydantic import BaseModel
from typing import List, Optional
import datetime

router = APIRouter(prefix="/locations", tags=["Locations"])

class LocationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    risk_level: Optional[str] = "low"  # low, medium, high
    lat: float
    lng: float

class LocationOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    risk_level: str
    lat: float
    lng: float
    created_at: datetime.datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[LocationOut])
def get_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Location).all()

@router.get("/{location_id}", response_model=LocationOut)
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location junction not found")
    return loc

@router.post("", response_model=LocationOut)
def create_location(
    payload: LocationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    # Check duplicate
    exists = db.query(Location).filter(Location.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Junction name already registered")

    loc = Location(
        name=payload.name,
        description=payload.description,
        risk_level=payload.risk_level,
        lat=payload.lat,
        lng=payload.lng
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)

    # Audit log
    audit = ActivityLog(
        user_id=admin.id,
        action=f"Registered new location: {loc.name} (Risk: {loc.risk_level})"
    )
    db.add(audit)
    db.commit()

    return loc

@router.put("/{location_id}", response_model=LocationOut)
def update_location(
    location_id: int,
    payload: LocationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    loc.name = payload.name
    loc.description = payload.description
    loc.risk_level = payload.risk_level
    loc.lat = payload.lat
    loc.lng = payload.lng

    db.commit()
    db.refresh(loc)

    # Audit log
    audit = ActivityLog(
        user_id=admin.id,
        action=f"Updated location specifications for {loc.name}"
    )
    db.add(audit)
    db.commit()

    return loc

@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    name = loc.name
    db.delete(loc)
    db.commit()

    # Audit log
    audit = ActivityLog(
        user_id=admin.id,
        action=f"Deleted location checkpoint: {name}"
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": f"Deleted location {name}."}
