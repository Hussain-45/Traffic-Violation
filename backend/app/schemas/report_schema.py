"""
Report Pydantic Validation Schemas
==================================
Defines validation, request filters, and output serialization schemas for report files.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReportFilterSchema(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    vehicle_type: Optional[str] = None
    violation_type: Optional[str] = None
    camera_id: Optional[str] = None
    license_plate: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    module: Optional[str] = None
    operator: Optional[str] = None


class ReportBase(BaseModel):
    title: str
    report_type: str  # daily, weekly, monthly, custom, vehicle, etc.
    start_date: datetime
    end_date: datetime
    format: str = "csv"  # pdf, csv, xlsx, json
    filters: Optional[ReportFilterSchema] = None


class ReportCreate(ReportBase):
    pass


class ReportResponse(BaseModel):
    id: int
    title: str
    generated_by: int
    report_type: str
    start_date: datetime
    end_date: datetime
    file_path: str
    status: str
    format: str
    filters: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class ReportTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    supported_formats: List[str]
    parameters: List[str]
