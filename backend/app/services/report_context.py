"""
Shared ReportContext Layer
==========================
Defines the unified data payload structure containing all stats, KPIs, and metadata
used for generating system documents.
"""
from typing import Dict, Any, List, Optional
import datetime


class ReportContext:
    """
    Houses all necessary parameters, metrics, and metadata to generate reports.
    Decouples raw DB query services from document formatting engines.
    """

    def __init__(
        self,
        report_id: int,
        generated_by: int,
        report_type: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        filters_applied: Dict[str, Any],
        kpis: Dict[str, Any],
        violation_distribution: List[Dict[str, Any]],
        vehicle_distribution: List[Dict[str, Any]],
        version: str = "1.0.0",
        checksum: Optional[str] = None
    ):
        self.report_id = report_id
        self.generated_by = generated_by
        self.report_type = report_type
        self.start_date = start_date
        self.end_date = end_date
        self.filters_applied = filters_applied or {}
        self.kpis = kpis or {}
        self.violation_distribution = violation_distribution or []
        self.vehicle_distribution = vehicle_distribution or []
        self.version = version
        self.generated_time = datetime.datetime.utcnow()
        self.checksum = checksum

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the ReportContext to a dictionary."""
        return {
            "report_id": self.report_id,
            "version": self.version,
            "generated_time": self.generated_time.isoformat(),
            "generated_by": self.generated_by,
            "report_type": self.report_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "filters_applied": self.filters_applied,
            "kpis": self.kpis,
            "violation_distribution": self.violation_distribution,
            "vehicle_distribution": self.vehicle_distribution,
            "checksum": self.checksum
        }
