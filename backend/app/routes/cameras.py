from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Camera, User, ActivityLog
from backend.app.auth.jwt import get_current_user, check_admin_role
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cameras", tags=["Cameras"])

class CameraCreate(BaseModel):
    id: str = Field(..., example="CAM-101")
    name: str = Field(..., example="North Junction CCTV 1")
    location: str = Field(..., example="Connaught Place, New Delhi")
    ip_address: Optional[str] = Field(None, example="192.168.1.100")
    status: str = Field("online", example="online") # online, offline
    health_status: str = Field("good", example="good") # good, warning, critical
    lat: float = Field(..., example=28.6304)
    lng: float = Field(..., example=77.2177)

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    health_status: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class CameraOut(BaseModel):
    id: str
    name: str
    location: str
    ip_address: Optional[str]
    status: str
    health_status: str
    lat: float
    lng: float

    class Config:
        from_attributes = True

@router.get("", response_model=List[CameraOut])
def get_cameras(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Camera).all()

@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
def create_camera(
    camera_in: CameraCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    db_camera = db.query(Camera).filter(Camera.id == camera_in.id).first()
    if db_camera:
        raise HTTPException(
            status_code=400,
            detail=f"Camera with ID {camera_in.id} already exists"
        )
    
    new_camera = Camera(**camera_in.model_dump())
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    
    # Audit Log
    log = ActivityLog(
        user_id=admin.id,
        action=f"Registered camera: {new_camera.id} at {new_camera.location}"
    )
    db.add(log)
    db.commit()
    
    return new_camera

@router.put("/{camera_id}", response_model=CameraOut)
def update_camera(
    camera_id: str,
    camera_in: CameraUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    update_data = camera_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)
        
    db.commit()
    db.refresh(camera)
    
    # Audit Log
    log = ActivityLog(
        user_id=admin.id,
        action=f"Updated camera: {camera.id}"
    )
    db.add(log)
    db.commit()
    
    return camera

@router.delete("/{camera_id}")
def delete_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    db.delete(camera)
    db.commit()
    
    # Audit Log
    log = ActivityLog(
        user_id=admin.id,
        action=f"Deleted camera: {camera_id}"
    )
    db.add(log)
    db.commit()
    
    return {"success": True, "message": f"Camera {camera_id} successfully deleted."}
