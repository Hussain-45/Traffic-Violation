"""
Unit Tests for Report Context, Storage, Templates, and Async Processors
=======================================================================
Asserts:
  1. Standardized ReportContext creation and serialization.
  2. StorageAdapter LocalFileSystem save/get operations.
  3. Decoupled template rendering strategies (Executive, Violation, Analytics, System).
  4. BackgroundTasks asynchronous compilation, checksum, and version audits.
  5. Download tracking counts and 410 expiry error handling.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, BackgroundTasks
from fastapi.testclient import TestClient
import datetime
import os
import hashlib

from backend.app.database import Base
from backend.main import app
from backend.app.models import Violation, Vehicle, Camera, User, Report
from backend.app.services.report_service import report_service
from backend.app.services.report_template_service import report_template_service
from backend.app.services.report_context import ReportContext
from backend.app.schemas.report_schema import ReportCreate, ReportFilterSchema

# Use a clean file-based SQLite database for testing report operations
test_db_filename = "test_reports.db"
test_engine = create_engine(f"sqlite:///{test_db_filename}", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

mock_user = User(id=9, username="test_reporter", email="rep@gmail.com", full_name="Test Reporter", password_hash="hash", status="active")


@pytest.fixture(autouse=True)
def setup_test_database():
    # Remove old test DB if it exists
    if os.path.exists(test_db_filename):
        try:
            os.remove(test_db_filename)
        except Exception:
            pass

    # Ensure reports directory exists
    os.makedirs(os.path.join("data", "reports"), exist_ok=True)
            
    # Recreate tables for each test run
    Base.metadata.create_all(bind=test_engine)
    
    # Seed mock data
    db = TestSessionLocal()
    db.add(mock_user)
    
    # Create Cameras
    c1 = Camera(id="CAM_01", name="Main Gate", location="GPS: 10,20", status="online", lat=10.0, lng=20.0)
    db.add(c1)
    
    # Create Vehicles
    v1 = Vehicle(id=1, license_plate="MH12AB1234", type="car", brand="Toyota")
    db.add(v1)
    
    # Create Violations
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
    db.add(vi1)
    
    db.commit()
    db.close()
    
    report_service.session_maker = TestSessionLocal
    yield
    report_service.session_maker = None
    Base.metadata.drop_all(bind=test_engine)
    
    # Clean up test database file
    if os.path.exists(test_db_filename):
        try:
            os.remove(test_db_filename)
        except Exception:
            pass
            
    # Clean up generated test reports
    reports_dir = os.path.join("data", "reports")
    if os.path.exists(reports_dir):
        for f in os.listdir(reports_dir):
            if f.startswith("report_"):
                try:
                    os.remove(os.path.join(reports_dir, f))
                except Exception:
                    pass


def test_report_context_serialization():
    ctx = ReportContext(
        report_id=101,
        generated_by=9,
        report_type="executive_report",
        start_date=datetime.datetime(2026, 7, 1),
        end_date=datetime.datetime(2026, 7, 10),
        filters_applied={"severity": "high"},
        kpis={"total_violations": 5},
        violation_distribution=[{"name": "No Helmet", "value": 5}],
        vehicle_distribution=[{"name": "motorbike", "value": 5}],
        version="1.2.0",
        checksum="abcd1234"
    )
    
    serialized = ctx.to_dict()
    assert serialized["report_id"] == 101
    assert serialized["version"] == "1.2.0"
    assert serialized["filters_applied"]["severity"] == "high"
    assert serialized["checksum"] == "abcd1234"


def test_template_strategies():
    templates = report_template_service.get_available_templates()
    ids = [t["id"] for t in templates]
    assert "executive_report" in ids
    assert "violation_report" in ids
    assert "analytics_report" in ids
    assert "system_report" in ids

    # Test rendering ViolationTemplate
    t_violation = report_template_service.get_template("violation_report")
    output = t_violation.render(
        title="Audit",
        start="2026-07-01",
        end="2026-07-10",
        kpis={},
        violations=[{"name": "Seat Belt", "value": 12}],
        vehicles=[]
    )
    assert "DETAILED VIOLATION REPORT" in output
    assert "Seat Belt" in output


def test_async_generation_and_storage():
    db = TestSessionLocal()
    bg = BackgroundTasks()

    payload = ReportCreate(
        title="Async Audit Report",
        report_type="executive_report",
        start_date=datetime.datetime(2026, 7, 1),
        end_date=datetime.datetime(2026, 7, 10),
        format="pdf",
        filters=ReportFilterSchema()
    )

    report = report_service.generate_report(db, user_id=9, payload=payload, background_tasks=bg)
    assert report.status == "generating"

    # Force background task execution inline
    task = bg.tasks[0]
    task.kwargs["db"] = db
    task.func(*task.args, **task.kwargs)

    # Refresh DB record
    db.refresh(report)
    assert report.status == "completed"
    assert report.checksum is not None
    assert report.version == "1.0.0"

    # Verify physical file exists and matches checksum
    filename = os.path.basename(report.file_path)
    physical_path = os.path.join("data", "reports", filename)
    assert os.path.exists(physical_path)
    
    with open(physical_path, "rb") as f:
        file_bytes = f.read()
        calculated = hashlib.sha256(file_bytes).hexdigest()
        assert calculated == report.checksum

    db.close()


def test_api_report_endpoints():
    from backend.app.database import get_db
    from backend.app.auth.jwt import get_current_user
    
    # Setup dependency overrides for FastAPI TestClient
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    def override_get_current_user(db: Session = Depends(override_get_db)):
        user = db.query(User).filter(User.username == "test_reporter").first()
        if not user:
            user = User(
                id=9,
                username="test_reporter",
                email="rep@gmail.com",
                full_name="Test Reporter",
                password_hash="hash",
                status="active"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
        
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        client = TestClient(app)

        # 1. Fetch available templates
        res = client.get("/api/v1/reports/templates")
        assert res.status_code == 200
        assert len(res.json()) > 0

        # 2. Trigger report generation
        payload = {
            "title": "API Daily Summary",
            "report_type": "daily_summary",
            "start_date": "2026-07-01T00:00:00",
            "end_date": "2026-07-10T23:59:59",
            "format": "pdf",
            "filters": {}
        }
        res = client.post("/api/v1/reports/generate", json=payload)
        assert res.status_code == 201
        report_data = res.json()
        assert report_data["status"] == "generating"
        report_id = report_data["id"]

        # Simulate async worker finishing the report
        db = TestSessionLocal()
        report_service.process_report_async(report_id, 9, {
            "start_date": "2026-07-01T00:00:00",
            "end_date": "2026-07-10T23:59:59",
            "filters": {}
        })
        db.close()

        # 3. Download generated file and assert download count incremented
        res = client.get(f"/api/v1/reports/download/{report_id}")
        assert res.status_code == 200
        assert "application/pdf" in res.headers["content-type"]

        db = TestSessionLocal()
        r = report_service.get_report(db, report_id)
        assert r.download_count == 1
        db.close()

        # 4. Test Expiration check: set expires_at in the past
        db = TestSessionLocal()
        r_db = report_service.get_report(db, report_id)
        r_db.expires_at = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        db.commit()
        db.close()

        res = client.get(f"/api/v1/reports/download/{report_id}")
        assert res.status_code == 410
        res_json = res.json()
        error_msg = res_json.get("detail") or res_json.get("message") or ""
        assert "expired" in error_msg

    finally:
        app.dependency_overrides.clear()
