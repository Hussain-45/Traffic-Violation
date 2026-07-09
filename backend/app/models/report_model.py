"""
Report SQLAlchemy ORM Model
============================
Defines the database schema for generating and tracking system reports (daily, weekly, monthly).
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Report(Base):
    """
    SQLAlchemy model representing the 'reports' database table.
    Stores metadata for generated files (PDF, CSV, Excel, JSON).
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(String, nullable=False)  # daily, weekly, monthly, custom, vehicle, violation, etc.
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="completed", index=True)  # pending, generating, completed, failed
    format = Column(String, default="csv", index=True)  # pdf, csv, xlsx, json
    filters = Column(JSON, nullable=True)  # Serializable filter dictionary
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="reports")
