"""
Evidence Pydantic Schemas
=========================
Defines input validation and output serialization schemas for Evidence records.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class EvidenceBase(BaseModel):
    evidence_id: str
    violation_id: str
    tracking_id: int
    verified_plate: Optional[str] = None
    vehicle_class: int
    violation_type: str
    severity: str
    timestamp: float
    frame_id: int
    camera_id: str
    location: str
    confidence: float
    original_frame_path: str
    annotated_frame_path: str
    vehicle_crop_path: Optional[str] = None
    plate_crop_path: Optional[str] = None
    hash: str
    evidence_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="metadata")

    @model_validator(mode="before")
    @classmethod
    def map_orm_metadata(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            model_dict = {}
            for col in data.__table__.columns:
                if col.name == "metadata":
                    model_dict["metadata"] = data.evidence_metadata
                else:
                    model_dict[col.name] = getattr(data, col.name)
            return model_dict
        return data


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    verified_plate: Optional[str] = None
    severity: Optional[str] = None
    evidence_metadata: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")


class EvidenceResponse(EvidenceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True
