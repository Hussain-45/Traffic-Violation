from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime

class VideoJobCreate(BaseModel):
    filename: str
    enabled_modules: List[str]
    confidence_threshold: float = 0.45
    tracking_threshold: float = 0.45
    ocr_threshold: float = 0.45
    max_fps: int = 30
    device: str = "cpu"  # cpu or gpu

class VideoJobOut(BaseModel):
    id: int
    filename: str
    original_video_path: str
    processed_video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    status: str
    progress: float
    total_frames: int
    processed_frames: int
    vehicles_detected: int
    violations_detected: int
    processing_fps: float
    processing_time: float
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    created_by: int
    report_path: Optional[str] = None
    annotated_video_path: Optional[str] = None
    error_message: Optional[str] = None
    timestamps: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
