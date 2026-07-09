"""
Detection Result Schema
=======================
Standardized output schema for every AI detection module.
Helmet, Seat Belt, Mobile Phone, and all future modules return this structure.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    """
    Standardized payload for an AI pipeline module's detection output.
    """
    module_name: str = Field(..., description="Name of the AI module (e.g. 'helmet_detection', 'seat_belt_detection', 'mobile_phone_detection')")
    tracking_id: int = Field(..., description="Unique track ID of the associated vehicle")
    vehicle_class: int = Field(..., description="Vehicle class ID from tracking (e.g. 2=car, 3=motorcycle)")
    region: List[float] = Field(..., description="Bounding box coordinates of the evaluation region [x1, y1, x2, y2]")
    status: str = Field(..., description="Status classification result (e.g. 'Seat Belt', 'No Seat Belt', 'Unknown', 'Mobile Phone')")
    confidence: float = Field(..., description="Detection confidence score (0.0 to 1.0)")
    timestamp: float = Field(..., description="Timestamp of the evaluated frame")
    frame_id: int = Field(..., description="ID of the evaluated frame")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra key-value metadata")

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the DetectionResult model to a plain Python dictionary.
        """
        return self.model_dump()
