import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.role_model import user_roles


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="officer")  # text fallback for backward compatibility
    status = Column(String, default="active")  # active, inactive
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Account Lockout & Failed Logins Trackings
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Relationships
    logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    roles_rel = relationship("Role", secondary=user_roles, back_populates="users")
    sessions_rel = relationship("SessionModel", back_populates="user", cascade="all, delete-orphan")
