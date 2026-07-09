"""
Analytics Report SQLAlchemy ORM Model
=====================================
Defines the database schema for saving pre-computed analytics snapshots and reports.
"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from backend.app.database import Base


class AnalyticsReportModel(Base):
    """
    SQLAlchemy model representing the 'analytics_reports' database table.
    Caches historical summary reports to avoid redundant aggregations.
    """
    __tablename__ = "analytics_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # daily, weekly, monthly, custom
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    summary_data = Column(JSON, nullable=False)  # Holds pre-computed JSON metrics
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
