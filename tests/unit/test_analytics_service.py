"""
Unit Tests for Analytics Repository, Service, and API Endpoints
===============================================================
Asserts:
  1. KPI calculations (totals, average confidence, active cameras).
  2. Chronological daily/weekly/monthly trend groupings.
  3. Class distribution counts (vehicle type, violation type).
  4. Offender rankings and camera activity sorting.
  5. HTML/CSV/Excel/JSON export generation.
  6. Filter parameters validation.
  7. API route endpoints integration.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import datetime

from backend.app.database import Base
from backend.main import app
from backend.app.models import Violation, Vehicle, Camera, User
from backend.app.models.email_log_model import EmailLogModel
from backend.app.services.analytics_service import analytics_service
from backend.app.repositories.analytics_repository import AnalyticsRepository
from backend.app.schemas.analytics_schema import AnalyticsReportCreate

# Set up clean in-memory SQLite database for testing analytics operations
test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_database():
    # Recreate tables in-memory for each test run
    Base.metadata.create_all(bind=test_engine)
    
    # Seed mock data
    db = TestSessionLocal()
    
    # 1. Create User
    user = User(id=1, username="officer_test", email="test@test.com", full_name="Officer Test", password_hash="hash")
    db.add(user)
    
    # 2. Create Cameras
    c1 = Camera(id="CAM_01", name="Main Gate", location="GPS: 10,20", status="online", lat=10.0, lng=20.0)
    c2 = Camera(id="CAM_02", name="Exit Gate", location="GPS: 30,40", status="online", lat=30.0, lng=40.0)
    db.add_all([c1, c2])
    
    # 3. Create Vehicles
    v1 = Vehicle(id=1, license_plate="MH12AB1234", type="car", brand="Toyota")
    v2 = Vehicle(id=2, license_plate="DL3C4567", type="motorcycle", brand="Honda")
    db.add_all([v1, v2])
    
    # 4. Create Violations
    vi1 = Violation(
        id=1,
        vehicle_id=1,
        camera_id="CAM_01",
        type="No Seat Belt",
        timestamp=datetime.datetime(2026, 7, 9, 10, 0, 0),
        location="GPS: 10,20",
        fine_amount=500.0,
        status="pending",
        confidence_score=0.88
    )
    vi2 = Violation(
        id=2,
        vehicle_id=2,
        camera_id="CAM_01",
        type="No Helmet",
        timestamp=datetime.datetime(2026, 7, 9, 11, 0, 0),
        location="GPS: 10,20",
        fine_amount=1000.0,
        status="pending",
        confidence_score=0.95
    )
    vi3 = Violation(
        id=3,
        vehicle_id=2,
        camera_id="CAM_02",
        type="No Helmet",
        timestamp=datetime.datetime(2026, 7, 8, 14, 0, 0),
        location="GPS: 30,40",
        fine_amount=1000.0,
        status="resolved",
        confidence_score=0.91
    )
    db.add_all([vi1, vi2, vi3])

    # 5. Create Email Logs
    e1 = EmailLogModel(id=1, evidence_id="EVID_01", violation_id="1", recipient="violator@gmail.com", subject="Notice 1", status="sent")
    e2 = EmailLogModel(id=2, evidence_id="EVID_02", violation_id="2", recipient="violator@gmail.com", subject="Notice 2", status="failed")
    db.add_all([e1, e2])

    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_repository_kpis():
    db = TestSessionLocal()
    repo = AnalyticsRepository(db)

    # All KPIs
    kpis = repo.get_kpis({})
    assert kpis["total_violations"] == 3
    assert kpis["total_vehicles"] == 2
    assert kpis["active_cameras"] == 2
    assert kpis["total_fines"] == 2500.0
    assert pytest.approx(kpis["avg_confidence"], 0.01) == 0.913

    # Filtered KPIs
    kpis_filtered = repo.get_kpis({"status": "resolved"})
    assert kpis_filtered["total_violations"] == 1
    assert kpis_filtered["total_fines"] == 1000.0

    db.close()


def test_repository_trends_and_distributions():
    db = TestSessionLocal()
    repo = AnalyticsRepository(db)

    # Trends grouping by day
    trends = repo.get_trends("day", {})
    assert len(trends) >= 2  # 2026-07-08 and 2026-07-09

    # Violation distribution
    violations_dist = repo.get_violation_distribution({})
    assert len(violations_dist) == 2
    assert violations_dist[0]["name"] == "No Helmet"
    assert violations_dist[0]["value"] == 2

    # Vehicle distribution
    vehicle_dist = repo.get_vehicle_distribution({})
    assert len(vehicle_dist) == 2

    db.close()


def test_top_rankings_and_emails():
    db = TestSessionLocal()
    repo = AnalyticsRepository(db)

    # Top Offenders
    offenders = repo.get_top_offenders(limit=2)
    assert len(offenders) == 2
    assert offenders[0]["plate"] == "DL3C4567"
    assert offenders[0]["violation_count"] == 2

    # Top Cameras
    cameras = repo.get_top_cameras(limit=2)
    assert len(cameras) == 2
    assert cameras[0]["camera_id"] == "CAM_01"
    assert cameras[0]["violation_count"] == 2

    # Emails
    emails = repo.get_email_statistics()
    assert emails["sent"] == 1
    assert emails["failed"] == 1

    db.close()


def test_analytics_service_dashboard():
    db = TestSessionLocal()
    summary = analytics_service.get_dashboard_summary(db, {})
    
    assert summary["kpis"]["total_violations"] == 3
    assert summary["kpis"]["total_fines"] == 2500.0
    assert summary["email_delivery_stats"]["sent"] == 1
    assert summary["performance_metrics"]["avg_processing_latency_ms"] == 142.5

    db.close()


def test_exports():
    db = TestSessionLocal()
    
    # 1. CSV
    content, media, fname = analytics_service.generate_export(db, {}, "csv")
    assert media == "text/csv"
    assert "License Plate" in content
    assert "MH12AB1234" in content

    # 2. JSON
    content, media, fname = analytics_service.generate_export(db, {}, "json")
    assert media == "application/json"
    assert "MH12AB1234" in content

    # 3. PDF (ASCII text layout)
    content, media, fname = analytics_service.generate_export(db, {}, "pdf")
    assert media == "application/pdf"
    assert "TRAFFIC VIOLATIONS REPORT" in content

    db.close()


def test_api_endpoints():
    from backend.app.database import get_db
    
    # Override get_db dependency in FastAPI app
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)

        # 1. Dashboard summary
        res = client.get("/api/v1/analytics/dashboard")
        assert res.status_code == 200
        data = res.json()
        assert data["kpis"]["total_violations"] == 3
        assert len(data["top_offenders"]) == 2

        # 2. Statistics
        res = client.get("/api/v1/analytics/statistics")
        assert res.status_code == 200
        assert res.json()["total_violations"] == 3

        # 3. Trends
        res = client.get("/api/v1/analytics/trends?interval=day")
        assert res.status_code == 200
        assert len(res.json()) >= 2

        # 4. Exports CSV
        res = client.get("/api/v1/analytics/export?format=csv")
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert "Violation ID" in res.text

        # 5. System Health
        res = client.get("/api/v1/analytics/health")
        assert res.status_code == 200
        assert res.json()["db_connection"] == "good"
    finally:
        app.dependency_overrides.clear()
