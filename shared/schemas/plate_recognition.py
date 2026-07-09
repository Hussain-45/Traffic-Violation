"""
Plate Recognition Schema
========================
Strongly-typed Pydantic models representing OCR candidates and plate recognition states.
Used by PlateRecognitionService and downstream OCR / ANPR modules.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class OCRCandidate(BaseModel):
    """
    Metadata representation of an OCR plate text candidate.
    """
    recognized_text: str = Field(..., description="Raw text returned by the OCR engine")
    normalized_text: str = Field(..., description="Cleaned, standardized plate text")
    confidence: float = Field(..., description="OCR confidence score")
    engine_name: str = Field(..., description="Name of the OCR engine (e.g. EasyOCR, PaddleOCR)")
    timestamp: float = Field(..., description="Timestamp of the detection frame")
    frame_id: int = Field(..., description="Frame index of the detection")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra attributes")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PlateRecognitionState(BaseModel):
    """
    Temporal recognition history and stable voting state for a tracked vehicle.
    """
    vehicle_tracking_id: int = Field(..., description="Unique track ID of the vehicle")
    stable_plate: Optional[str] = Field(default=None, description="Confirmed stable plate text after voting")
    recognition_history: List[OCRCandidate] = Field(default_factory=list, description="Historical list of OCR candidate readings")
    best_candidate: Optional[OCRCandidate] = Field(default=None, description="Candidate with highest aggregated confidence")
    aggregated_confidence: float = Field(default=0.0, description="Confidence score resolved over multiple frames")
    vote_count: int = Field(default=0, description="Number of frames voting for the stable plate text")
    validation_status: str = Field(default="Unknown", description="Registration validation code (Valid, Possibly Valid, Invalid, Unknown)")
    timestamp: float = Field(..., description="Timestamp of the latest update")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra metrics")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
