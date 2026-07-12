import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

from backend.app.models.user_model import User
from backend.app.models.role_model import Role
from backend.app.models.permission_model import Permission
from backend.app.models.session_model import SessionModel


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    risk_level = Column(String, default="low")  # low, medium, high
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cameras = relationship("Camera", back_populates="location_rel")


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String, primary_key=True, index=True)  # e.g., CAM-001
    name = Column(String, nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    location = Column(String, nullable=False)  # Text fallback
    ip_address = Column(String, nullable=True)
    status = Column(String, default="online")  # online, offline
    health_status = Column(String, default="good")  # good, warning, critical
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    location_rel = relationship("Location", back_populates="cameras")
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
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    location = Column(String, nullable=False)
    fine_amount = Column(Float, nullable=False)
    status = Column(String, default="pending", index=True)  # pending, paid, resolved
    evidence_image_path = Column(String, nullable=True)
    evidence_video_path = Column(String, nullable=True)
    confidence_score = Column(Float, default=1.0)
    officer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

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



class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)
    description = Column(String, nullable=True)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String, nullable=True)

    user = relationship("User", back_populates="logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # fine, officer, system, camera
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="notifications")


from backend.app.models.email_log_model import EmailLogModel
from backend.app.models.analytics_model import AnalyticsReportModel
from backend.app.models.evidence_model import EvidenceModel
from backend.app.models.report_model import Report
from backend.app.models.video_analysis_model import AnalysisJob
