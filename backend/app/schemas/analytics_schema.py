"""
Analytics Pydantic Schemas
==========================
Defines validation and output serialization structures for metrics, trends, and reports.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AnalyticsReportBase(BaseModel):
    report_name: str
    report_type: str
    start_date: datetime
    end_date: datetime
    summary_data: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsReportCreate(AnalyticsReportBase):
    pass


class AnalyticsReportResponse(AnalyticsReportBase):
    id: int
    created_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class KPICardData(BaseModel):
    total_violations: int
    total_vehicles: int
    active_cameras: int
    total_fines: float
    avg_confidence: float
    db_health: str
    system_uptime: str


class TrendItem(BaseModel):
    date: str
    count: int
    fines: float


class DistributionItem(BaseModel):
    name: str
    value: int


class OffenderRanking(BaseModel):
    plate: str
    violation_count: int


class CameraActivity(BaseModel):
    camera_id: str
    location: str
    violation_count: int


class DashboardSummaryResponse(BaseModel):
    kpis: KPICardData
    daily_trends: List[TrendItem]
    weekly_trends: List[TrendItem]
    monthly_trends: List[TrendItem]
    violation_distribution: List[DistributionItem]
    vehicle_distribution: List[DistributionItem]
    top_offenders: List[OffenderRanking]
    top_cameras: List[CameraActivity]
    email_delivery_stats: Dict[str, int]
    rule_specific_stats: Dict[str, Dict[str, Any]]
    performance_metrics: Dict[str, Any]
