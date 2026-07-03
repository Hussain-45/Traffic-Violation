from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import User, ActivityLog
from backend.app.auth.jwt import get_current_user, check_admin_role
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/users", tags=["Users"])

class UserUpdate(BaseModel):
    status: str # active, inactive
    role: str # admin, officer

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    status: str

    class Config:
        from_attributes = True

class LogOut(BaseModel):
    id: int
    action: str
    timestamp: str
    username: str

@router.get("", response_model=List[UserOut])
def get_users(
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    return db.query(User).all()

@router.put("/{user_id}", response_model=UserOut)
def update_user_privilege(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot edit your own status/role")
        
    user.status = payload.status
    user.role = payload.role
    db.commit()
    db.refresh(user)
    
    # Audit log
    log = ActivityLog(
        user_id=admin.id,
        action=f"Updated privileges of user: {user.username} (status: {user.status}, role: {user.role})"
    )
    db.add(log)
    db.commit()
    
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
    db.delete(user)
    db.commit()
    
    # Audit log
    log = ActivityLog(
        user_id=admin.id,
        action=f"Deleted user account: {user.username}"
    )
    db.add(log)
    db.commit()
    
    return {"success": True, "message": f"User {user.username} deleted."}

@router.get("/logs", response_model=List[dict])
def get_activity_logs(
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(100).all()
    results = []
    for l in logs:
        results.append({
            "id": l.id,
            "username": l.user.username,
            "action": l.action,
            "timestamp": l.timestamp.isoformat()
        })
    return results
