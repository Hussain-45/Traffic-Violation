from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import FineRule, Payment, Violation, User, ActivityLog
from backend.app.auth.jwt import get_current_user
from pydantic import BaseModel
from typing import List, Optional
import datetime
import uuid

router = APIRouter(prefix="/fines", tags=["Fine Management"])

# Pydantic Schemas
class FineRuleOut(BaseModel):
    id: int
    violation_type: str
    amount: float
    description: Optional[str] = None

    class Config:
        from_attributes = True

class FineRuleUpdate(BaseModel):
    amount: float
    description: Optional[str] = None

class PaymentCreate(BaseModel):
    violation_id: int
    payment_method: str  # credit_card, debit_card, upi, cash
    amount: float

class PaymentOut(BaseModel):
    id: int
    violation_id: int
    amount: float
    payment_date: datetime.datetime
    transaction_id: str
    payment_method: str
    status: str

    class Config:
        from_attributes = True

# Helper function to seed fine rules if empty
def seed_fine_rules_if_empty(db: Session):
    count = db.query(FineRule).count()
    if count == 0:
        default_rules = [
            FineRule(violation_type="red_light_jump", amount=2000.0, description="Passing intersection when light signal is red"),
            FineRule(violation_type="wrong_lane", amount=1000.0, description="Driving in incorrect designated road lanes"),
            FineRule(violation_type="overspeeding", amount=1000.0, description="Exceeding target highway speed limits"),
            FineRule(violation_type="no_helmet", amount=500.0, description="Riding a two-wheeler vehicle without wearing a helmet"),
            FineRule(violation_type="no_seatbelt", amount=500.0, description="Driving a passenger vehicle without a buckled seatbelt"),
            FineRule(violation_type="triple_riding", amount=1000.0, description="Riding a two-wheeler vehicle with more than 2 passengers"),
            FineRule(violation_type="against_traffic", amount=2000.0, description="Driving in the wrong direction of flow"),
            FineRule(violation_type="illegal_parking", amount=500.0, description="Parking in designated restricted or towing zones")
        ]
        db.add_all(default_rules)
        db.commit()

# --- Fine Rules Endpoints ---

@router.get("/rules", response_model=List[FineRuleOut])
def get_fine_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    seed_fine_rules_if_empty(db)
    return db.query(FineRule).all()

@router.put("/rules/{rule_id}", response_model=FineRuleOut)
def update_fine_rule(
    rule_id: int,
    payload: FineRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify traffic fine rules."
        )

    rule = db.query(FineRule).filter(FineRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Fine rule not found")

    rule.amount = payload.amount
    if payload.description is not None:
        rule.description = payload.description

    db.commit()
    db.refresh(rule)

    # Log action
    log = ActivityLog(
        user_id=current_user.id,
        action=f"Updated fine tariff rule for {rule.violation_type} to ₹{rule.amount}"
    )
    db.add(log)
    db.commit()

    return rule

# --- Payments Endpoints ---

@router.get("/payments", response_model=dict)
def get_payments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    payment_method: Optional[str] = None,
    status: Optional[str] = None,
    transaction_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payment)
    
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
    if status:
        query = query.filter(Payment.status == status)
    if transaction_id:
        query = query.filter(Payment.transaction_id.ilike(f"%{transaction_id}%"))
        
    total = query.count()
    payments = query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": payments,
        "skip": skip,
        "limit": limit
    }

@router.post("/payments", response_model=PaymentOut)
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    violation = db.query(Violation).filter(Violation.id == payload.violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation record not found")

    if violation.status == "paid":
        raise HTTPException(status_code=400, detail="This violation fine has already been settled.")

    # Create transaction log
    tx_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
    
    payment = Payment(
        violation_id=payload.violation_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        transaction_id=tx_id,
        status="completed"
    )
    
    db.add(payment)
    
    # Update violation status to paid
    violation.status = "paid"
    
    db.commit()
    db.refresh(payment)

    # Log action
    log = ActivityLog(
        user_id=current_user.id,
        action=f"Logged payment of ₹{payload.amount} for Violation #{payload.violation_id} (TXN: {tx_id})"
    )
    db.add(log)
    db.commit()

    return payment

@router.get("/payments/{payment_id}", response_model=PaymentOut)
def get_payment_details(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found")
    return payment
