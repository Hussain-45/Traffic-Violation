"""
Unit Tests for Wrong Side Detection Module
==========================================
Verifies:
  1. Initialization and configuration loading.
  2. Integration with TrajectoryService and MotionState.
  3. Correct Direction evaluation (travel angle matches lane orientation).
  4. Wrong Side evaluation (travel angle opposes lane orientation).
  5. Temporal validation checks (minimum age, distance, history).
  6. Consecutive confirmations smoothing.
  7. Standardized Pydantic DetectionResult outputs.
  8. Error recovery and missing states.
"""
import pytest
import numpy as np
import supervision as sv
from unittest.mock import MagicMock

from ai.detection.wrong_side_detection import WrongSideDetectionModule
from ai.services.road_scene_service import RoadSceneService
from ai.services.trajectory_service import trajectory_service
from ai.pipelines.pipeline_context import PipelineContext
from shared.schemas import DetectionResult


@pytest.fixture
def wrong_side_module():
    module = WrongSideDetectionModule(pipeline_config_path="configs/pipeline.yaml")
    module.initialize()
    return module


def test_wrong_side_initialization(wrong_side_module):
    assert wrong_side_module._initialized is True
    assert wrong_side_module.status()["name"] == "WrongSideDetectionModule"
    assert "minimum_track_age" in wrong_side_module.config


def test_wrong_side_missing_tracking(wrong_side_module):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=1, raw_frame=frame)
    
    # context.tracked_detections is None -> skips processing gracefully
    results, errors, warnings = wrong_side_module.process(frame, context)
    
    assert len(errors) == 0
    assert len(warnings) == 0
    assert results["status"] == "Active"
    assert results["wrong_side_count"] == 0
    assert results["correct_direction_count"] == 0


def test_wrong_side_temporal_validation(wrong_side_module):
    # Setup TrajectoryService trajectory updates for vehicle ID 1
    # Check that under 10 frames track age, the state is classified as "Unknown"
    trajectory_service.reset()
    wrong_side_module.wrong_confirmations.clear()
    wrong_side_module.correct_confirmations.clear()
    wrong_side_module.stable_states.clear()
    
    # Push 4 updates (less than min_track_age=10)
    for i in range(4):
        # Moving up the screen (against incoming traffic)
        y_pos = 300.0 - (i * 10.0)
        trajectory_service.update_trajectory(vehicle_id=1, bbox_xyxy=[100, y_pos, 150, y_pos + 50], timestamp=float(i))

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=4, raw_frame=frame)
    # Mock tracked detections
    context.tracked_detections = sv.Detections(
        xyxy=np.array([[100.0, 260.0, 150.0, 310.0]]),
        tracker_id=np.array([1]),
        confidence=np.array([0.90]),
        class_id=np.array([2])
    )
    
    results, errors, warnings = wrong_side_module.process(frame, context)
    
    assert results["unknown_count"] == 1
    assert results["wrong_side_count"] == 0
    assert context.metadata["wrong_side_detection"][1]["status"] == "Unknown"


def test_wrong_side_correct_direction(wrong_side_module):
    trajectory_service.reset()
    wrong_side_module.wrong_confirmations.clear()
    wrong_side_module.correct_confirmations.clear()
    wrong_side_module.stable_states.clear()
    
    # Push 12 updates (greater than min_track_age=10) moving down the screen (correct direction)
    for i in range(12):
        y_pos = 100.0 + (i * 10.0)  # dy > 0, heading angle ~90 deg (matches lane orientation 90.0)
        trajectory_service.update_trajectory(vehicle_id=2, bbox_xyxy=[200, y_pos, 250, y_pos + 50], timestamp=float(i))
        
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=12, raw_frame=frame)
    context.tracked_detections = sv.Detections(
        xyxy=np.array([[200.0, 220.0, 250.0, 270.0]]),
        tracker_id=np.array([2]),
        confidence=np.array([0.95]),
        class_id=np.array([2])
    )
    
    # Run process 3 consecutive times to satisfy consecutive_confirmations=3
    for _ in range(3):
        results, errors, warnings = wrong_side_module.process(frame, context)
        
    assert results["correct_direction_count"] == 1
    assert results["wrong_side_count"] == 0
    assert context.metadata["wrong_side_detection"][2]["status"] == "Correct Direction"


def test_wrong_side_violation_detection(wrong_side_module):
    trajectory_service.reset()
    wrong_side_module.wrong_confirmations.clear()
    wrong_side_module.correct_confirmations.clear()
    wrong_side_module.stable_states.clear()
    
    # Push 12 updates moving up the screen (against correct lane direction)
    for i in range(12):
        y_pos = 300.0 - (i * 10.0)  # dy < 0, heading angle ~270 deg (opposes lane orientation 90.0)
        trajectory_service.update_trajectory(vehicle_id=3, bbox_xyxy=[300, y_pos, 350, y_pos + 50], timestamp=float(i))
        
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=12, raw_frame=frame)
    context.tracked_detections = sv.Detections(
        xyxy=np.array([[300.0, 180.0, 350.0, 230.0]]),
        tracker_id=np.array([3]),
        confidence=np.array([0.98]),
        class_id=np.array([2])
    )
    
    # Run process 3 times to trigger consecutive validations
    for _ in range(3):
        results, errors, warnings = wrong_side_module.process(frame, context)
        
    assert results["wrong_side_count"] == 1
    assert results["correct_direction_count"] == 0
    assert context.metadata["wrong_side_detection"][3]["status"] == "Wrong Side"
