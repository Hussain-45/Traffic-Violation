"""
Evidence SQLAlchemy ORM Model
==============================
Defines the database schema and indexing strategy for storing violation evidence records.
"""
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from backend.app.database import Base


class EvidenceModel(Base):
    """
    SQLAlchemy model representing the 'evidences' database table.
    """
    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String, unique=True, index=True, nullable=False)
    violation_id = Column(String, index=True, nullable=False)
    tracking_id = Column(Integer, index=True, nullable=False)
    verified_plate = Column(String, index=True, nullable=True)
    vehicle_class = Column(Integer, nullable=False)
    violation_type = Column(String, index=True, nullable=False)
    severity = Column(String, index=True, nullable=False)
    timestamp = Column(Float, index=True, nullable=False)
    frame_id = Column(Integer, nullable=False)
    camera_id = Column(String, nullable=False)
    location = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    original_frame_path = Column(String, nullable=False)
    annotated_frame_path = Column(String, nullable=False)
    vehicle_crop_path = Column(String, nullable=True)
    plate_crop_path = Column(String, nullable=True)
    hash = Column(String, unique=True, index=True, nullable=False)
    
    # Map the JSON column name exactly as 'metadata' in SQL to satisfy specifications,
    # but use 'evidence_metadata' in Python to prevent collision with Base.metadata.
    evidence_metadata = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
