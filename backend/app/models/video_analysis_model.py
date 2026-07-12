import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_video_path = Column(String, nullable=False)
    processed_video_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    status = Column(String, default="pending", index=True)  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)
    total_frames = Column(Integer, default=0)
    processed_frames = Column(Integer, default=0)
    vehicles_detected = Column(Integer, default=0)
    violations_detected = Column(Integer, default=0)
    processing_fps = Column(Float, default=0.0)
    processing_time = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_path = Column(String, nullable=True)
    annotated_video_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    timestamps = Column(Text, nullable=True)  # JSON representation of events list
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User")
