"""
Unit Tests for DatabaseService & Repository
===========================================
Verifies:
  1. CRUD operations in EvidenceRepository.
  2. Transaction rollbacks on model insertion failures.
  3. Idempotent writes & duplicate record prevention in DatabaseService.
  4. Advanced search, pagination, and statistics query logic.
  5. Connection health check responsiveness.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

from backend.app.database import Base
from backend.app.services.database_service import DatabaseService
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence_schema import EvidenceCreate, EvidenceUpdate
from shared.schemas.evidence_record import EvidenceRecord

# Set up clean in-memory SQLite database
test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_database():
    # Recreate tables in-memory for each test run
    Base.metadata.create_all(bind=test_engine)
    with patch("backend.app.services.database_service.SessionLocal", TestSessionLocal):
        yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def clean_service():
    service = DatabaseService()
    return service


def test_repository_crud():
    db = TestSessionLocal()
    repo = EvidenceRepository(db)

    schema = EvidenceCreate(
        evidence_id="ev-uuid-01",
        violation_id="viol-uuid-01",
        tracking_id=10,
        verified_plate="MH12DE1234",
        vehicle_class=3,
        violation_type="No Helmet",
        severity="Medium",
        timestamp=100.0,
        frame_id=5,
        camera_id="CAM_01",
        location="GPS: 10, 20",
        confidence=0.88,
        original_frame_path="/paths/orig.jpg",
        annotated_frame_path="/paths/ann.jpg",
        vehicle_crop_path="/paths/v.jpg",
        plate_crop_path="/paths/p.jpg",
        hash="hash-signature-01",
        metadata={"camera": "CAM_01"}
    )

    # 1. Create (autobegin manages transaction start)
    db_obj = repo.create(schema)
    db.commit()

    assert db_obj.id is not None
    assert db_obj.evidence_id == "ev-uuid-01"
    assert db_obj.verified_plate == "MH12DE1234"

    # 2. Get
    fetched = repo.get_by_evidence_id("ev-uuid-01")
    assert fetched is not None
    assert fetched.violation_type == "No Helmet"

    # 3. Update
    repo.update(db_obj.id, EvidenceUpdate(verified_plate="MH12DE9999", severity="High"))
    db.commit()

    updated = repo.get(db_obj.id)
    assert updated.verified_plate == "MH12DE9999"
    assert updated.severity == "High"

    # 4. Search by Plate
    results = repo.find_by_plate("DE999")
    assert len(results) == 1

    # 5. Delete
    success = repo.delete(db_obj.id)
    db.commit()
    assert success is True
    assert repo.get(db_obj.id) is None

    db.close()


def test_database_service_idempotence(clean_service):
    rec = EvidenceRecord(
        evidence_id="ev-idempotent-99",
        violation_id="viol-idempotent-99",
        tracking_id=20,
        verified_plate="KA01AB1234",
        vehicle_class=2,
        violation_type="Wrong Side",
        severity="High",
        timestamp=200.0,
        frame_id=10,
        camera_id="CAM_02",
        location="GPS: 12, 77",
        confidence=0.95,
        original_frame_path="/p/o.jpg",
        annotated_frame_path="/p/a.jpg",
        vehicle_crop_path="/p/v.jpg",
        plate_crop_path="/p/p.jpg",
        evidence_status="Generated",
        hash="hash-idempotent-99",
        metadata={}
    )

    # First insert
    res1 = clean_service.insert_evidence(rec)
    assert res1 is not None
    assert res1.evidence_id == "ev-idempotent-99"

    # Second insert of exact same record (should skip duplicate and return first)
    res2 = clean_service.insert_evidence(rec)
    assert res2 is not None
    assert res2.id == res1.id


def test_transaction_rollback_on_failure(clean_service):
    rec = EvidenceRecord(
        evidence_id="ev-rollback-99",
        violation_id="viol-rollback-99",
        tracking_id=30,
        verified_plate=None,
        vehicle_class=2,
        violation_type="No Seat Belt",
        severity="Low",
        timestamp=300.0,
        frame_id=20,
        camera_id="CAM_03",
        location="GPS: 13, 78",
        confidence=0.82,
        original_frame_path="/p/o.jpg",
        annotated_frame_path="/p/a.jpg",
        evidence_status="Generated",
        hash="hash-rollback-99",
        metadata={}
    )

    # Induce model creation failure (e.g. mock repo.create to throw Exception)
    with patch.object(EvidenceRepository, "create", side_effect=ValueError("Simulated DB Error")):
        res = clean_service.insert_evidence(rec)
        assert res is None

    # Verify no records saved
    db = TestSessionLocal()
    repo = EvidenceRepository(db)
    assert repo.get_by_evidence_id("ev-rollback-99") is None
    db.close()


def test_search_and_pagination(clean_service):
    db = TestSessionLocal()
    repo = EvidenceRepository(db)
    
    # Insert 5 test records
    for i in range(5):
        schema = EvidenceCreate(
            evidence_id=f"ev-idx-{i}",
            violation_id=f"viol-idx-{i}",
            tracking_id=i,
            verified_plate=f"MH12AB100{i}",
            vehicle_class=2,
            violation_type="Wrong Side" if i % 2 == 0 else "No Helmet",
            severity="High" if i % 2 == 0 else "Medium",
            timestamp=400.0 + i,
            frame_id=100 + i,
            camera_id="CAM_01",
            location="GPS: 10, 20",
            confidence=0.90,
            original_frame_path="/p/o.jpg",
            annotated_frame_path="/p/a.jpg",
            hash=f"hash-idx-{i}",
            metadata={}
        )
        repo.create(schema)
    db.commit()
    db.close()

    # Search page 1, size 3
    results, total = clean_service.search_evidence(page=1, page_size=3)
    assert total == 5
    assert len(results) == 3

    # Filter search by wrong side
    results_ws, total_ws = clean_service.search_evidence(violation_type="Wrong Side")
    assert total_ws == 3


def test_statistics(clean_service):
    db = TestSessionLocal()
    repo = EvidenceRepository(db)
    
    # Insert 3 test records with various classes
    repo.create(EvidenceCreate(
        evidence_id="ev-stat-01", violation_id="viol-stat-01", tracking_id=1,
        vehicle_class=2, violation_type="Wrong Side", severity="High",
        timestamp=500.0, frame_id=200, camera_id="CAM_01", location="GPS: 0,0",
        confidence=0.90, original_frame_path="/p/o.jpg", annotated_frame_path="/p/a.jpg",
        hash="hash-stat-01", metadata={}
    ))
    repo.create(EvidenceCreate(
        evidence_id="ev-stat-02", violation_id="viol-stat-02", tracking_id=2,
        vehicle_class=2, violation_type="Wrong Side", severity="High",
        timestamp=501.0, frame_id=201, camera_id="CAM_01", location="GPS: 0,0",
        confidence=0.90, original_frame_path="/p/o.jpg", annotated_frame_path="/p/a.jpg",
        hash="hash-stat-02", metadata={}
    ))
    repo.create(EvidenceCreate(
        evidence_id="ev-stat-03", violation_id="viol-stat-03", tracking_id=3,
        vehicle_class=3, violation_type="No Helmet", severity="Medium",
        timestamp=502.0, frame_id=202, camera_id="CAM_01", location="GPS: 0,0",
        confidence=0.90, original_frame_path="/p/o.jpg", annotated_frame_path="/p/a.jpg",
        hash="hash-stat-03", metadata={}
    ))
    db.commit()
    db.close()

    stats = clean_service.get_statistics()
    assert stats["total_records"] == 3
    assert stats["violations_breakdown"]["Wrong Side"] == 2
    assert stats["violations_breakdown"]["No Helmet"] == 1
    assert stats["severity_breakdown"]["High"] == 2


def test_health_check(clean_service):
    assert clean_service.health_check() is True
