"""
Unit Tests for Plate Association Service
=========================================
Verifies:
  1. Initialization and configurations.
  2. Single plate-to-vehicle association.
  3. Stable plate generation (5 confirmations).
  4. Ambiguous association resolution (highest score match).
  5. Scalability performance (100 vehicles, 100 plates).
  6. Historical state cleanup for stale tracking IDs.
"""
import pytest
import time
from loguru import logger

from ai.services.plate_association_service import plate_association_service


@pytest.fixture(autouse=True)
def clean_service():
    plate_association_service.reset()
    yield


def test_plate_association_initialization():
    assert plate_association_service.config is not None
    assert "minimum_plate_confidence" in plate_association_service.config


def test_plate_association_basic_mapping():
    vehicles = [
        {"id": 10, "bbox": [100.0, 100.0, 300.0, 300.0], "class_id": 2, "conf": 0.90}
    ]
    plates = [
        {"id": None, "bbox": [150.0, 250.0, 250.0, 290.0], "conf": 0.85, "cropped_image": None}
    ]

    plate_association_service.associate_all(vehicles, plates, timestamp=100.0, frame_id=1)
    
    assoc = plate_association_service.get_association(10)
    assert assoc is not None
    assert assoc.associated_plate is not None
    assert assoc.associated_plate.confidence == 0.85
    assert len(assoc.plate_history) == 1
    assert assoc.stable_plate is None


def test_plate_association_stable_generation():
    vehicles = [
        {"id": 20, "bbox": [100.0, 100.0, 300.0, 300.0], "class_id": 2, "conf": 0.90}
    ]

    # Feed 5 frames of detections to trigger stable plate selection
    for f_id in range(1, 6):
        conf = 0.80 + (f_id * 0.02) # varying confidence (max at frame 5 is 0.90)
        plates = [
            {"id": None, "bbox": [150.0, 250.0, 250.0, 290.0], "conf": conf, "cropped_image": None}
        ]
        plate_association_service.associate_all(vehicles, plates, timestamp=100.0 + f_id, frame_id=f_id)

    assoc = plate_association_service.get_association(20)
    assert assoc is not None
    assert len(assoc.plate_history) == 5
    assert assoc.stable_plate is not None
    assert assoc.stable_plate.confidence == 0.90  # Highest confidence plate selected


def test_plate_association_ambiguous_resolution():
    vehicles = [
        {"id": 30, "bbox": [100.0, 100.0, 300.0, 300.0], "class_id": 2, "conf": 0.90},
        {"id": 40, "bbox": [250.0, 100.0, 450.0, 300.0], "class_id": 2, "conf": 0.88}
    ]
    plates = [
        {"id": None, "bbox": [150.0, 250.0, 230.0, 290.0], "conf": 0.85, "cropped_image": None} # closer to 30
    ]

    plate_association_service.associate_all(vehicles, plates, timestamp=100.0, frame_id=1)

    assoc_30 = plate_association_service.get_association(30)
    assoc_40 = plate_association_service.get_association(40)

    assert assoc_30.associated_plate is not None
    assert assoc_40 is None or assoc_40.associated_plate is None


def test_plate_association_cleanup():
    vehicles = [
        {"id": 50, "bbox": [100.0, 100.0, 300.0, 300.0], "class_id": 2, "conf": 0.90}
    ]
    plates = [
        {"id": None, "bbox": [150.0, 250.0, 250.0, 290.0], "conf": 0.85, "cropped_image": None}
    ]

    # Associate once
    plate_association_service.associate_all(vehicles, plates, timestamp=100.0, frame_id=1)
    assert plate_association_service.get_association(50) is not None

    # Next frame vehicle 50 is lost (not in list)
    plate_association_service.associate_all(vehicles=[], plates=[], timestamp=101.0, frame_id=2)
    assert plate_association_service.get_association(50) is None


def test_plate_association_performance():
    vehicles = []
    plates = []

    for i in range(100):
        offset = i * 200.0
        vehicles.append({
            "id": i,
            "bbox": [offset, 100.0, offset + 150.0, 300.0],
            "class_id": 2,
            "conf": 0.90
        })
        plates.append({
            "id": None,
            "bbox": [offset + 50.0, 250.0, offset + 100.0, 280.0],
            "conf": 0.85,
            "cropped_image": None
        })

    start_time = time.perf_counter()
    plate_association_service.associate_all(vehicles, plates, timestamp=200.0, frame_id=1)
    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000.0
    logger.info(f"Association performance for 100 vehicles, 100 plates: {elapsed_ms:.2f}ms")
    
    # Performance assertion
    assert elapsed_ms < 150.0
    
    # Check that i-th vehicle has its plate
    assoc = plate_association_service.get_association(42)
    assert assoc is not None
    assert assoc.associated_plate is not None
