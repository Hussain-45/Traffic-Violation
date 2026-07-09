"""
Plate Association Schema
========================
Strongly-typed Pydantic models representing number plate info and vehicle associations.
Used by PlateAssociationService and Number Plate Detection.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PlateInfo(BaseModel):
    """
    Metadata representation of a detected number plate.
    """
    plate_tracking_id: Optional[int] = Field(default=None, description="Unique track ID of the plate if tracked")
    plate_bbox: List[float] = Field(..., description="Plate bounding box coordinates [x1, y1, x2, y2]")
    confidence: float = Field(..., description="Detection confidence score of the plate box")
    cropped_plate_image: Optional[Any] = Field(default=None, description="Image array of the cropped plate (optional)")
    timestamp: float = Field(..., description="Timestamp of the detection frame")
    frame_id: int = Field(..., description="Frame index of the detection")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra attributes")

    model_config = {
        "arbitrary_types_allowed": True
    }

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class VehiclePlateAssociation(BaseModel):
    """
    Standardized payload grouping a vehicle with its associated number plate.
    """
    vehicle_tracking_id: int = Field(..., description="Unique track ID of the vehicle")
    vehicle_class: int = Field(..., description="Vehicle class ID (e.g. car, truck, motorcycle)")
    vehicle_bbox: List[float] = Field(..., description="Vehicle bounding box coordinates [x1, y1, x2, y2]")
    associated_plate: Optional[PlateInfo] = Field(default=None, description="Currently associated plate (current frame)")
    association_confidence: float = Field(default=0.0, description="Group association confidence score")
    plate_history: List[PlateInfo] = Field(default_factory=list, description="Historical list of associated plates for stability")
    stable_plate: Optional[PlateInfo] = Field(default=None, description="Confirmed stable plate over multiple frames")
    timestamp: float = Field(..., description="Timestamp of the evaluated frame")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra metrics")

    model_config = {
        "arbitrary_types_allowed": True
    }

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
