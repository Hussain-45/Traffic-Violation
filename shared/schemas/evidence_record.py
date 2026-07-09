"""
Evidence Record Schema
======================
Strongly-typed Pydantic model representing generated evidence packages for violations.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class EvidenceRecord(BaseModel):
    """
    Standardized payload for violation evidence.
    """
    evidence_id: str = Field(..., description="Unique UUID identifying this evidence package")
    violation_id: str = Field(..., description="UUID of the triggering ViolationRecord")
    tracking_id: int = Field(..., description="Track ID of the associated vehicle")
    verified_plate: Optional[str] = Field(default=None, description="Verified license plate text")
    vehicle_class: int = Field(..., description="Vehicle class ID")
    violation_type: str = Field(..., description="Type of violation")
    severity: str = Field(..., description="Severity of violation")
    timestamp: float = Field(..., description="UNIX timestamp of decision")
    frame_id: int = Field(..., description="Frame index of decision")
    camera_id: str = Field(..., description="Camera ID or video source identifier")
    location: str = Field(..., description="GPS coordinates or location name")
    confidence: float = Field(..., description="Aggregated confidence score")
    original_frame_path: str = Field(..., description="Local file path to the saved original frame")
    annotated_frame_path: str = Field(..., description="Local file path to the saved annotated frame")
    vehicle_crop_path: Optional[str] = Field(default=None, description="Local file path to the vehicle crop")
    plate_crop_path: Optional[str] = Field(default=None, description="Local file path to the license plate crop")
    evidence_status: str = Field(..., description="Status of the evidence package (e.g. 'Generated')")
    hash: str = Field(..., description="SHA-256 hash of the evidence package files for tamper protection")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata log")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
