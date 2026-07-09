"""
Unit Tests for Seat Belt Detection Module
=========================================
Verifies:
  1. Initialization and configuration loading.
  2. Windshield subdivision and occupant evaluation logic (Seat Belt, No Seat Belt, Unknown states).
  3. Proper filtering (ignores motorcycles/bicycles/pedestrians, only processes car/truck/bus).
  4. Integration metrics and counts.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock
from ai.detection.seatbelt_detection import SeatBeltDetectionModule
from ai.pipelines.pipeline_context import PipelineContext
import supervision as sv


@pytest.fixture
def mock_seatbelt_module():
    module = SeatBeltDetectionModule(models_config_path="configs/models.yaml")
    module.initialize()
    return module


def test_seatbelt_module_initialization(mock_seatbelt_module):
    assert mock_seatbelt_module._initialized is True
    assert hasattr(mock_seatbelt_module, "active_size")
    assert mock_seatbelt_module.status()["name"] == "SeatBeltDetectionModule"


def test_seatbelt_module_graceful_missing_weights(monkeypatch):
    import os
    # Mock os.path.exists to return False so weights are reported missing
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    module = SeatBeltDetectionModule(models_config_path="configs/non_existent_models_config.yaml")
    module.initialize()
    
    # Verify model is None and health reports False, but initialize is True (no crash)
    assert module._initialized is True
    assert module.model is None
    assert module.health() is False
    
    # Process a frame and verify warning is emitted
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=1, raw_frame=frame)
    results, errors, warnings = module.process(frame, context)
    
    assert len(warnings) > 0
    assert "warning" in warnings[0]["message"].lower() or "missing" in warnings[0]["message"].lower()
    assert results["status"] == "Inactive"


def test_windshield_subdivision_and_matching(mock_seatbelt_module):
    # 1. Mock YOLO model inside the module
    mock_model = MagicMock()
    mock_seatbelt_module.model = mock_model
    
    # 2. Setup mock YOLO boxes:
    # Box 1: Seatbelt (cls=2) at [210, 110, 240, 160] (falls in Driver region [200, 100, 300, 200])
    # Box 2: Mobile Phone (cls=3) at [120, 110, 140, 130] (falls in Passenger region [100, 100, 200, 200])
    box1 = MagicMock()
    box1.cls = [MagicMock(item=lambda: 2)]
    box1.conf = [MagicMock(item=lambda: 0.95)]
    box1.xyxy = [MagicMock(tolist=lambda: [210.0, 110.0, 240.0, 160.0])]
    
    box2 = MagicMock()
    box2.cls = [MagicMock(item=lambda: 3)]
    box2.conf = [MagicMock(item=lambda: 0.88)]
    box2.xyxy = [MagicMock(tolist=lambda: [120.0, 110.0, 140.0, 130.0])]
    
    mock_results = MagicMock()
    mock_results.boxes = [box1, box2]
    mock_model.return_value = [mock_results]
    
    # 3. Create context with tracked detections:
    # Track 1: Car (class_id=2) at [100, 100, 300, 300], ID 18
    # Track 2: Motorcycle (class_id=3) at [400, 100, 500, 300], ID 12 (should be ignored!)
    xyxy = np.array([
        [100.0, 100.0, 300.0, 300.0],
        [400.0, 100.0, 500.0, 300.0]
    ], dtype=np.float32)
    
    class_id = np.array([2, 3], dtype=int)
    tracker_id = np.array([18, 12], dtype=int)
    confidence = np.array([0.9, 0.9], dtype=np.float32)
    
    tracked_detections = sv.Detections(
        xyxy=xyxy,
        class_id=class_id,
        tracker_id=tracker_id,
        confidence=confidence
    )
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(
        frame_id=1,
        raw_frame=frame,
        working_frame=frame.copy()
    )
    context.tracked_detections = tracked_detections
    
    # 4. Execute process
    results, errors, warnings = mock_seatbelt_module.process(frame, context)
    
    # 5. Verify results
    assert len(errors) == 0
    assert len(warnings) == 0
    assert results["status"] == "Active"
    
    # Verify counts
    # Driver (Right): Seat Belt (class 2 found)
    # Passenger (Left): No Seat Belt (class 3 found, class 2 missing)
    # Ignored: Motorcycle 12
    assert results["seat_belt_count"] == 1
    assert results["no_seat_belt_count"] == 1
    assert results["unknown_count"] == 0
    
    # Verify violators list
    assert len(results["violators"]) == 1
    assert results["violators"][0]["vehicle_id"] == 18
    assert results["violators"][0]["driver_violator"] is False
    assert results["violators"][0]["passenger_violator"] is True
    
    # Verify metadata
    assert "seat_belt_detection" in context.metadata
    sb_data = context.metadata["seat_belt_detection"]
    assert 18 in sb_data
    assert sb_data[18]["driver"]["status"] == "Seat Belt"
    assert sb_data[18]["passenger"]["status"] == "No Seat Belt"
    assert 12 not in sb_data  # Motorcycle is ignored
