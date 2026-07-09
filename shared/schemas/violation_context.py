"""
Violation Context Schemas
==========================
Pydantic schemas representing the aggregated violation context and history entries for tracked vehicles.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ViolationHistoryEntry(BaseModel):
    """
    Standardized history entry representing a single frame-level violation detection.
    """
    module_name: str = Field(..., description="Name of the AI module (e.g. 'helmet_detection', 'wrong_side_detection')")
    status: str = Field(..., description="Classification result status (e.g. 'No Helmet', 'Wrong Side')")
    confidence: float = Field(..., description="Detection confidence score (0.0 to 1.0)")
    timestamp: float = Field(..., description="Timestamp of the detection frame")
    frame_id: int = Field(..., description="Frame index of the detection")
    tracking_id: int = Field(..., description="Track ID of the associated vehicle")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra attributes")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class VehicleViolationContext(BaseModel):
    """
    Unified state container representing the aggregation of all AI module outputs,
    temporal history, confidence, and verification states for a single tracked vehicle.
    """
    tracking_id: int = Field(..., description="Unique track ID of the vehicle")
    vehicle_class: int = Field(..., description="Vehicle class ID (e.g. 2=car, 3=motorcycle)")
    verified_plate: Optional[str] = Field(default=None, description="Verified license plate number text")
    timestamp: float = Field(..., description="Timestamp of the last evaluated frame")
    frame_id: int = Field(..., description="Frame index of the last evaluation")

    # Detection Status
    helmet_status: str = Field(default="Unknown", description="Helmet detection status")
    seatbelt_status: str = Field(default="Unknown", description="Seatbelt detection status")
    phone_status: str = Field(default="Unknown", description="Mobile phone usage status")
    wrong_side_status: str = Field(default="Unknown", description="Wrong side driving status")
    signal_status: str = Field(default="Unknown", description="Traffic signal compliance status")
    triple_riding_status: str = Field(default="Unknown", description="Triple riding occupancy status")

    # Detection Confidence
    helmet_confidence: float = Field(default=0.0, description="Helmet status confidence score")
    seatbelt_confidence: float = Field(default=0.0, description="Seatbelt status confidence score")
    phone_confidence: float = Field(default=0.0, description="Mobile phone status confidence score")
    wrong_side_confidence: float = Field(default=0.0, description="Wrong side status confidence score")
    signal_confidence: float = Field(default=0.0, description="Traffic signal status confidence score")
    triple_riding_confidence: float = Field(default=0.0, description="Triple riding status confidence score")

    # Temporal History
    violation_history: List[ViolationHistoryEntry] = Field(default_factory=list, description="List of individual violation detections")
    first_seen: float = Field(..., description="Timestamp of when the vehicle was first tracked")
    last_seen: float = Field(..., description="Timestamp of when the vehicle was last seen")
    frame_count: int = Field(default=0, description="Total number of frames this vehicle has been tracked")

    # Evidence & Verification States
    evidence_ready: bool = Field(default=False, description="Flag indicating if the context is ready for challan generation")
    stable_detection: bool = Field(default=False, description="Flag indicating if the state is temporally stable")
    verification_state: str = Field(default="Processing", description="Overall verification state ('Processing', 'Verified', 'No Violation')")

    # Extra Attributes
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Consolidated extra metadata across modules")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
