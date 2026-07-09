"""
Rider and Motorcycle Group Schema
==================================
Strongly-typed Pydantic models representing motorcycle groups and associated riders.
Used by RiderAssociationService, Helmet Detection, and Triple Riding Detection.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RiderInfo(BaseModel):
    """
    Metadata representation of an associated motorcycle rider (driver or passenger).
    """
    rider_tracking_id: int = Field(..., description="Unique track ID of the rider (person)")
    rider_type: str = Field(..., description="Rider classification role: 'driver', 'passenger', or 'unknown'")
    bounding_box: List[float] = Field(..., description="Rider bounding box coordinates [x1, y1, x2, y2]")
    confidence: float = Field(..., description="Detection confidence score of the rider box")
    helmet_status: Optional[str] = Field(default=None, description="Helmet status if evaluated ('Helmet', 'No Helmet', 'Unknown')")
    position_index: int = Field(default=0, description="Horizontal/Vertical sorting order index on the motorcycle (0 = front/driver)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra attributes")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class MotorcycleGroup(BaseModel):
    """
    Standardized payload grouping a motorcycle with its associated occupant riders.
    """
    motorcycle_tracking_id: int = Field(..., description="Unique track ID of the motorcycle")
    motorcycle_bbox: List[float] = Field(..., description="Motorcycle bounding box coordinates [x1, y1, x2, y2]")
    driver: Optional[RiderInfo] = Field(default=None, description="Identified driver of the motorcycle (closest to front)")
    passengers: List[RiderInfo] = Field(default_factory=list, description="List of passengers sorted from front to back")
    rider_count: int = Field(default=0, description="Total count of associated riders (driver + passengers)")
    confidence: float = Field(default=1.0, description="Group association confidence score")
    timestamp: float = Field(..., description="Timestamp of the evaluated frame")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra metrics")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
