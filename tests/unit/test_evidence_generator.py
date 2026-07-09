"""
Unit Tests for EvidenceGenerator
===============================
Verifies:
  1. Config loading and directory initialization.
  2. Frame and crop extraction (vehicle crops, plate crops).
  3. SHA-256 integrity hash calculation.
  4. Missing crop gracefulness (plate_crop_path is None).
  5. Error recovery when frame is invalid.
"""
import pytest
import os
import shutil
import numpy as np
import cv2
import supervision as sv

from ai.violations.evidence_generator import EvidenceGenerator
from shared.schemas.violation_record import ViolationRecord
from ai.pipelines.pipeline_context import PipelineContext


@pytest.fixture
def temp_output_dir():
    dir_path = "outputs/test_evidence"
    os.makedirs(dir_path, exist_ok=True)
    yield dir_path
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


@pytest.fixture
def clean_generator(temp_output_dir):
    generator = EvidenceGenerator()
    generator.initialize()
    generator.output_dir = temp_output_dir
    return generator


def test_generator_initialization(clean_generator, temp_output_dir):
    assert clean_generator._initialized is True
    assert clean_generator.output_dir == temp_output_dir
    assert os.path.exists(temp_output_dir)


def test_process_evidence_generates_files(clean_generator, temp_output_dir):
    # Create dummy original BGR frame (red image)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:, :, 2] = 255  # Solid red

    # Bounding boxes
    # Vehicle: [50, 50, 200, 250]
    # License Plate: [70, 200, 150, 230]
    detections = sv.Detections(
        xyxy=np.array([[50.0, 50.0, 200.0, 250.0]]),
        class_id=np.array([3]),  # Motorcycle
        tracker_id=np.array([15])
    )

    ctx = PipelineContext(
        frame_id=100,
        timestamp=1000.0,
        raw_frame=frame,
        working_frame=frame.copy(),
        tracked_detections=detections
    )
    ctx.metadata["number_plate_detection"] = {
        15: {
            "metadata": {
                "plate_bbox": [70.0, 200.0, 150.0, 230.0]
            }
        }
    }

    violation = ViolationRecord(
        violation_id="test-violation-uuid",
        tracking_id=15,
        verified_plate="MH12DE1234",
        vehicle_class=3,
        violation_type="No Helmet",
        severity="Medium",
        confidence=0.88,
        timestamp=1000.0,
        frame_id=100,
        rule_id="RULE_HELMET_01",
        decision_status="Confirmed",
        evidence_required=True
    )

    evidence_records = clean_generator.process_evidence([violation], ctx)

    assert len(evidence_records) == 1
    rec = evidence_records[0]

    assert rec.violation_id == "test-violation-uuid"
    assert rec.tracking_id == 15
    assert rec.verified_plate == "MH12DE1234"
    assert rec.violation_type == "No Helmet"
    assert rec.evidence_status == "Generated"
    assert rec.hash != ""

    # Check that paths exist and are valid files
    assert os.path.exists(rec.original_frame_path)
    assert os.path.exists(rec.annotated_frame_path)
    assert os.path.exists(rec.vehicle_crop_path)
    assert os.path.exists(rec.plate_crop_path)

    # Verify vehicle crop size
    v_img = cv2.imread(rec.vehicle_crop_path)
    assert v_img.shape[0] == 200  # 250 - 50
    assert v_img.shape[1] == 150  # 200 - 50

    # Verify plate crop size
    p_img = cv2.imread(rec.plate_crop_path)
    assert p_img.shape[0] == 30   # 230 - 200
    assert p_img.shape[1] == 80   # 150 - 70


def test_process_evidence_graceful_missing_plate(clean_generator, temp_output_dir):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    detections = sv.Detections(
        xyxy=np.array([[50.0, 50.0, 200.0, 250.0]]),
        class_id=np.array([2]),  # Car
        tracker_id=np.array([16])
    )

    ctx = PipelineContext(
        frame_id=101,
        timestamp=1001.0,
        raw_frame=frame,
        working_frame=frame.copy(),
        tracked_detections=detections
    )
    # No number plate metadata for tracking ID 16

    violation = ViolationRecord(
        violation_id="test-violation-uuid-2",
        tracking_id=16,
        verified_plate=None,
        vehicle_class=2,
        violation_type="No Seat Belt",
        severity="Low",
        confidence=0.90,
        timestamp=1001.0,
        frame_id=101,
        rule_id="RULE_SEATBELT_01",
        decision_status="Confirmed",
        evidence_required=True
    )

    evidence_records = clean_generator.process_evidence([violation], ctx)

    assert len(evidence_records) == 1
    rec = evidence_records[0]

    assert rec.plate_crop_path is None
    assert os.path.exists(rec.original_frame_path)
    assert os.path.exists(rec.annotated_frame_path)
    assert os.path.exists(rec.vehicle_crop_path)


def test_process_evidence_invalid_frame_returns_empty(clean_generator):
    # Context with no raw frame
    ctx = PipelineContext(frame_id=102, timestamp=1002.0, raw_frame=None)
    violation = ViolationRecord(
        violation_id="test-violation-uuid-3",
        tracking_id=17,
        verified_plate=None,
        vehicle_class=2,
        violation_type="No Seat Belt",
        severity="Low",
        confidence=0.90,
        timestamp=1002.0,
        frame_id=102,
        rule_id="RULE_SEATBELT_01",
        decision_status="Confirmed",
        evidence_required=True
    )

    records = clean_generator.process_evidence([violation], ctx)
    assert len(records) == 0
