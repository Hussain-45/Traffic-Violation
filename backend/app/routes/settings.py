from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import FineRule, User, ActivityLog
from backend.app.auth.jwt import get_current_user, check_admin_role
from backend.app.config import settings
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/settings", tags=["Settings"])

class FineRuleOut(BaseModel):
    violation_type: str
    amount: float
    description: str

    class Config:
        from_attributes = True

class FineRuleUpdate(BaseModel):
    amount: float

class ThresholdUpdate(BaseModel):
    ai_mode: str  # active, simulated
    confidence_threshold: float
    speed_limit: float

@router.get("/fines", response_model=List[FineRuleOut])
def get_fine_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(FineRule).all()

@router.put("/fines/{violation_type}", response_model=FineRuleOut)
def update_fine_rule(
    violation_type: str,
    payload: FineRuleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    rule = db.query(FineRule).filter(FineRule.violation_type == violation_type).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Fine rule not found")
        
    old_amount = rule.amount
    rule.amount = payload.amount
    db.commit()
    db.refresh(rule)
    
    # Audit log
    log = ActivityLog(
        user_id=admin.id,
        action=f"Updated fine rule for '{violation_type}' from {old_amount} to {rule.amount}"
    )
    db.add(log)
    db.commit()
    
    return rule

@router.get("/thresholds")
def get_thresholds(current_user: User = Depends(get_current_user)):
    return {
        "ai_mode": settings.AI_MODE,
        "confidence_threshold": settings.AI_CONFIDENCE_THRESHOLD,
        "speed_limit": settings.SPEED_LIMIT_KMH
    }

@router.put("/thresholds")
def update_thresholds(
    payload: ThresholdUpdate,
    admin: User = Depends(check_admin_role)
):
    # Dynamic settings updates
    settings.AI_MODE = payload.ai_mode
    settings.AI_CONFIDENCE_THRESHOLD = payload.confidence_threshold
    settings.SPEED_LIMIT_KMH = payload.speed_limit
    
    return {
        "success": True,
        "message": "AI configurations updated successfully.",
        "settings": {
            "ai_mode": settings.AI_MODE,
            "confidence_threshold": settings.AI_CONFIDENCE_THRESHOLD,
            "speed_limit": settings.SPEED_LIMIT_KMH
        }
    }
