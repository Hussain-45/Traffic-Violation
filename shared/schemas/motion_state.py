"""
Motion State Model
==================
Strongly-typed Pydantic model representing a vehicle's motion trajectory state.
Encapsulates positions, motion vectors, angles, velocities, and predictions.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Position(BaseModel):
    """
    Standardized coordinate position payload.
    """
    x: float = Field(..., description="X-coordinate center")
    y: float = Field(..., description="Y-coordinate center")
    timestamp: float = Field(..., description="Timestamp of the position")
    frame_id: Optional[int] = Field(default=None, description="Frame ID of the position")

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


class MotionState(BaseModel):
    """
    Standardized vehicle motion state encapsulation.
    Replaces raw lists/dictionaries in TrajectoryService and downstream modules.
    """
    tracking_id: int = Field(..., description="Unique track ID of the vehicle")
    current_position: Position = Field(..., description="Current position of the vehicle center")
    previous_position: Optional[Position] = Field(default=None, description="Previous position of the vehicle center")
    motion_vector: List[float] = Field(default_factory=lambda: [0.0, 0.0], description="Displacement vector [dx, dy] over history")
    normalized_direction: List[float] = Field(default_factory=lambda: [0.0, 0.0], description="Unit direction vector [ndx, ndy]")
    travel_angle: Optional[float] = Field(default=None, description="Direction angle in degrees (0 to 360)")
    average_velocity: float = Field(default=0.0, description="Average velocity in pixels/second over history")
    instantaneous_velocity: float = Field(default=0.0, description="Instantaneous velocity in pixels/second")
    acceleration: float = Field(default=0.0, description="Acceleration in pixels/second^2")
    total_distance: float = Field(default=0.0, description="Accumulated travel distance in pixels")
    history_length: int = Field(default=0, description="Number of tracked coordinates in history")
    track_age: int = Field(default=0, description="Total number of frames tracked since creation")
    confidence: float = Field(default=1.0, description="Tracking confidence")
    predicted_position: Optional[Position] = Field(default=None, description="Linear prediction for the next position")
    timestamp: float = Field(..., description="Current evaluation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Module-specific extra metrics")

    def to_dict(self) -> Dict[str, Any]:
        """Converts the MotionState model to a plain Python dictionary."""
        return self.model_dump()
