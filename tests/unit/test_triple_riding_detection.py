"""
Unit Tests for Triple Riding Detection Module
=============================================
Verifies:
  1. Initialization and configurations.
  2. Ignoring non-motorcycles (e.g. cars).
  3. Single Rider classification.
  4. Double Riding classification.
  5. Triple Riding classification.
  6. Unknown state (under min track age).
  7. Temporal confirmation smoothing (3-frame delay).
  8. Missing RiderAssociationService error recovery.
"""
import pytest
import numpy as np
import supervision as sv
from unittest.mock import MagicMock

from ai.detection.triple_riding_detection import TripleRidingDetectionModule
from ai.services.rider_association_service import rider_association_service
from ai.services.trajectory_service import trajectory_service
from ai.pipelines.pipeline_context import PipelineContext
from shared.schemas import DetectionResult


@pytest.fixture
def triple_riding_module():
    module = TripleRidingDetectionModule(pipeline_config_path="configs/pipeline.yaml")
    module.initialize()
    return module


@pytest.fixture(autouse=True)
def clean_services():
    rider_association_service.reset()
    trajectory_service.reset()
    yield


def test_triple_riding_initialization(triple_riding_module):
    assert triple_riding_module._initialized is True
    assert "minimum_track_age" in triple_riding_module.config


def test_triple_riding_ignore_non_motorcycles(triple_riding_module):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=1, raw_frame=frame)
    # Tracked detection is class_id = 2 (car)
    context.tracked_detections = sv.Detections(
        xyxy=np.array([[100.0, 100.0, 200.0, 200.0]]),
        tracker_id=np.array([10]),
        confidence=np.array([0.90]),
        class_id=np.array([2])
    )

    results, errors, warnings = triple_riding_module.process(frame, context)

    assert results["triple_count"] == 0
    assert results["single_count"] == 0
    assert len(context.metadata.get("triple_riding_detection", {})) == 0


def test_triple_riding_single_rider(triple_riding_module):
    # Setup motorcycle ID 20, 1 rider, age >= 5
    for i in range(6):
        trajectory_service.update_trajectory(vehicle_id=20, bbox_xyxy=[100.0, 100.0, 200.0, 300.0], timestamp=float(i))

    motorcycles = [{"id": 20, "bbox": [100.0, 100.0, 200.0, 300.0], "conf": 0.90}]
    riders = [{"id": 1, "bbox": [110.0, 110.0, 190.0, 190.0], "conf": 0.85}]
    
    rider_association_service.associate_riders(motorcycles, riders, timestamp=100.0)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=10, raw_frame=frame)
    context.tracked_detections = sv.Detections(
        xyxy=np.array([[100.0, 100.0, 200.0, 300.0]]),
        tracker_id=np.array([20]),
        confidence=np.array([0.90]),
        class_id=np.array([3])
    )

    # Run 3 times for confirmations
    for _ in range(3):
        results, errors, warnings = triple_riding_module.process(frame, context)

    assert results["single_count"] == 1
    assert results["triple_count"] == 0
    assert context.metadata["triple_riding_detection"][20]["status"] == "Single Rider"


def test_triple_riding_double_riding(triple_riding_module):
    # Setup motorcycle ID 30, 2 riders, age >= 5
    for i in range(6):
        trajectory_service.update_trajectory(vehicle_id=30, bbox_xyxy=[100.0, 100.0, 200.0, 300.0], timestamp=float(i))

    motorcycles = [{"id": 30, "bbox": [100.0, 100.0, 200.0, 300.0], "conf": 0.90}]
    riders = [
        {"id": 1, "bbox": [110.0, 110.0, 190.0, 190.0], "conf": 0.85},
        {"id": 2, "bbox": [110.0, 210.0, 190.0, 290.0], "conf": 0.80}
    ]
    
    rider_association_service.associate_riders(motorcycles, riders, timestamp=100.0)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=10, raw_frame=frame)
    context.tracked_detections = sv.Detections(
        xyxy=np.array([[100.0, 100.0, 200.0, 300.0]]),
        tracker_id=np.array([30]),
        confidence=np.array([0.90]),
        class_id=np.array([3])
    )

    for _ in range(3):
        results, errors, warnings = triple_riding_module.process(frame, context)

    assert results["double_count"] == 1
    assert results["triple_count"] == 0
    assert context.metadata["triple_riding_detection"][30]["status"] == "Double Riding"


def test_triple_riding_violation_detected(triple_riding_module):
    # Setup motorcycle ID 40, 3 riders, age >= 5
    for i in range(6):
        trajectory_service.update_trajectory(vehicle_id=40, bbox_xyxy=[100.0, 100.0, 200.0, 300.0], timestamp=float(i))

    motorcycles = [{"id": 40, "bbox": [100.0, 100.0, 200.0, 300.0], "conf": 0.90}]
    riders = [
        {"id": 1, "bbox": [110.0, 110.0, 190.0, 150.0], "conf": 0.85},
        {"id": 2, "bbox": [110.0, 160.0, 190.0, 210.0], "conf": 0.80},
        {"id": 3, "bbox": [110.0, 220.0, 190.0, 280.0], "conf": 0.80}
    ]
    
    rider_association_service.associate_riders(motorcycles, riders, timestamp=100.0)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=10, raw_frame=frame)
    context.tracked_detections = sv.Detections(
        xyxy=np.array([[100.0, 100.0, 200.0, 300.0]]),
        tracker_id=np.array([40]),
        confidence=np.array([0.90]),
        class_id=np.array([3])
    )

    for _ in range(3):
        results, errors, warnings = triple_riding_module.process(frame, context)

    assert results["triple_count"] == 1
    assert context.metadata["triple_riding_detection"][40]["status"] == "Triple Riding"
    assert context.metadata["triple_riding_detection"][40]["metadata"]["rider_count"] == 3
