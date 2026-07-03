from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import FineRule, User, ActivityLog, Setting
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

def get_or_create_setting(db: Session, key: str, default_value: str, description: str = None) -> str:
    item = db.query(Setting).filter(Setting.key == key).first()
    if not item:
        item = Setting(key=key, value=default_value, description=description)
        db.add(item)
        db.commit()
        db.refresh(item)
    return item.value

def update_setting(db: Session, key: str, value: str) -> None:
    item = db.query(Setting).filter(Setting.key == key).first()
    if item:
        item.value = value
    else:
        item = Setting(key=key, value=value)
        db.add(item)
    db.commit()

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
def get_thresholds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ai_mode = get_or_create_setting(db, "ai_mode", settings.AI_MODE, "AI execution mode: active or simulated")
    conf_thresh = get_or_create_setting(db, "confidence_threshold", str(settings.AI_CONFIDENCE_THRESHOLD), "YOLO/OCR confidence limit")
    speed_limit = get_or_create_setting(db, "speed_limit", str(settings.SPEED_LIMIT_KMH), "Urban speed limit in km/h")

    # Sync memory settings
    settings.AI_MODE = ai_mode
    settings.AI_CONFIDENCE_THRESHOLD = float(conf_thresh)
    settings.SPEED_LIMIT_KMH = float(speed_limit)

    return {
        "ai_mode": ai_mode,
        "confidence_threshold": float(conf_thresh),
        "speed_limit": float(speed_limit)
    }

@router.put("/thresholds")
def update_thresholds(
    payload: ThresholdUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(check_admin_role)
):
    # Save settings in the database
    update_setting(db, "ai_mode", payload.ai_mode)
    update_setting(db, "confidence_threshold", str(payload.confidence_threshold))
    update_setting(db, "speed_limit", str(payload.speed_limit))

    # Sync memory configurations immediately
    settings.AI_MODE = payload.ai_mode
    settings.AI_CONFIDENCE_THRESHOLD = payload.confidence_threshold
    settings.SPEED_LIMIT_KMH = payload.speed_limit

    # Audit log
    log = ActivityLog(
        user_id=admin.id,
        action=f"Updated AI Thresholds: mode={payload.ai_mode}, conf={payload.confidence_threshold}, speed={payload.speed_limit}"
    )
    db.add(log)
    db.commit()

    return {
        "success": True,
        "message": "AI configurations updated successfully in Database.",
        "settings": {
            "ai_mode": payload.ai_mode,
            "confidence_threshold": payload.confidence_threshold,
            "speed_limit": payload.speed_limit
        }
    }
