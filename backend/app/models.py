import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="officer")  # admin, officer
    status = Column(String, default="active")  # active, inactive
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String, primary_key=True, index=True)  # e.g., CAM-001
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    status = Column(String, default="online")  # online, offline
    health_status = Column(String, default="good")  # good, warning, critical
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    violations = relationship("Violation", back_populates="camera")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=False)  # car, motorcycle, truck, bus, auto
    brand = Column(String, nullable=True)
    color = Column(String, nullable=True)
    owner_name = Column(String, nullable=True)
    status = Column(String, default="valid")  # valid, expired, stolen, suspended
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    violations = relationship("Violation", back_populates="vehicle")


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    type = Column(String, nullable=False)  # red_light_jump, wrong_lane, overspeeding, etc.
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    location = Column(String, nullable=False)
    fine_amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, paid, resolved
    evidence_image_path = Column(String, nullable=True)
    evidence_video_path = Column(String, nullable=True)
    confidence_score = Column(Float, default=1.0)
    officer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="violations")
    camera = relationship("Camera", back_populates="violations")
    payments = relationship("Payment", back_populates="violation", cascade="all, delete-orphan")


class FineRule(Base):
    __tablename__ = "fine_rules"

    id = Column(Integer, primary_key=True, index=True)
    violation_type = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.datetime.utcnow)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    payment_method = Column(String, nullable=False)  # credit_card, debit_card, upi, cash
    status = Column(String, default="completed")  # completed, failed, pending

    violation = relationship("Violation", back_populates="payments")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String, nullable=True)

    user = relationship("User", back_populates="logs")
