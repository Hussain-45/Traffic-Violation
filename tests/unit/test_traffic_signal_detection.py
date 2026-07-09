"""
Unit Tests for Traffic Signal Detection Module
==============================================
Verifies:
  1. Initialization and configuration loading.
  2. ROI filtering and spatial containment using RoadSceneService.
  3. Class mapping and lit state evaluation (Red, Yellow, Green, Unknown).
  4. Standardized Pydantic DetectionResult outputs.
  5. Graceful recovery when weights are missing.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock
from ai.detection.traffic_signal_detection import TrafficSignalDetectionModule
from ai.services.road_scene_service import RoadSceneService
from ai.pipelines.pipeline_context import PipelineContext
from shared.schemas import DetectionResult


@pytest.fixture
def mock_ts_module():
    module = TrafficSignalDetectionModule(models_config_path="configs/models.yaml")
    module.initialize()
    return module


def test_ts_module_initialization(mock_ts_module):
    assert mock_ts_module._initialized is True
    assert hasattr(mock_ts_module, "active_size")
    assert mock_ts_module.status()["name"] == "TrafficSignalDetectionModule"


def test_ts_module_graceful_missing_weights(monkeypatch):
    import os
    # Mock os.path.exists to return False so weights are reported missing
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    module = TrafficSignalDetectionModule(models_config_path="configs/non_existent_models_config.yaml")
    module.initialize()
    
    assert module._initialized is True
    assert module.model is None
    assert module.health() is False
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(frame_id=1, raw_frame=frame)
    results, errors, warnings = module.process(frame, context)
    
    assert len(warnings) > 0
    assert "warning" in warnings[0]["message"].lower() or "missing" in warnings[0]["message"].lower()
    assert results["status"] == "Inactive"


def test_road_scene_service_rois():
    w, h = 1920, 1080
    
    # 1. Traffic Light ROI is in the upper 45%
    tl_roi = RoadSceneService.get_traffic_light_roi(w, h)
    assert tl_roi == [0.0, 0.0, 1920.0, 486.0]
    
    # 2. Intersection ROI is middle/lower portion
    is_roi = RoadSceneService.get_intersection_roi(w, h)
    assert is_roi == [0.0, 378.0, 1920.0, 1026.0]
    
    # 3. Containment checks
    box_inside = [100.0, 100.0, 150.0, 200.0]  # Center (125, 150) -> inside tl_roi
    box_outside = [100.0, 500.0, 150.0, 600.0]  # Center (125, 550) -> outside tl_roi
    
    assert RoadSceneService.is_in_roi(box_inside, tl_roi) is True
    assert RoadSceneService.is_in_roi(box_outside, tl_roi) is False


def test_traffic_signal_classification(mock_ts_module):
    # 1. Mock YOLO model inside module
    mock_model = MagicMock()
    mock_ts_module.model = mock_model
    
    # 2. Setup mock YOLO boxes:
    # Box 1: Red light (cls=0) at [100, 100, 120, 180] (falls in ROI [0, 0, 640, 216] of 640x480 frame)
    # Box 2: Green light (cls=1) at [300, 100, 320, 180] (falls in ROI)
    # Box 3: Yellow light (cls=2) at [500, 100, 520, 180] (falls in ROI)
    # Box 4: Unknown light (cls=3) at [200, 100, 220, 180] (falls in ROI)
    # Box 5: Out of ROI light (cls=0) at [300, 300, 320, 380] (falls outside ROI -> ignored)
    box1 = MagicMock()
    box1.cls = [MagicMock(item=lambda: 0)]
    box1.conf = [MagicMock(item=lambda: 0.98)]
    box1.xyxy = [MagicMock(tolist=lambda: [100.0, 100.0, 120.0, 180.0])]
    
    box2 = MagicMock()
    box2.cls = [MagicMock(item=lambda: 1)]
    box2.conf = [MagicMock(item=lambda: 0.95)]
    box2.xyxy = [MagicMock(tolist=lambda: [300.0, 100.0, 320.0, 180.0])]
    
    box3 = MagicMock()
    box3.cls = [MagicMock(item=lambda: 2)]
    box3.conf = [MagicMock(item=lambda: 0.90)]
    box3.xyxy = [MagicMock(tolist=lambda: [500.0, 100.0, 520.0, 180.0])]
    
    box4 = MagicMock()
    box4.cls = [MagicMock(item=lambda: 3)]
    box4.conf = [MagicMock(item=lambda: 0.85)]
    box4.xyxy = [MagicMock(tolist=lambda: [200.0, 100.0, 220.0, 180.0])]
    
    box5 = MagicMock()
    box5.cls = [MagicMock(item=lambda: 0)]
    box5.conf = [MagicMock(item=lambda: 0.95)]
    box5.xyxy = [MagicMock(tolist=lambda: [300.0, 300.0, 320.0, 380.0])]
    
    mock_results = MagicMock()
    mock_results.boxes = [box1, box2, box3, box4, box5]
    mock_model.return_value = [mock_results]
    
    # 3. Create context
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    context = PipelineContext(
        frame_id=1,
        raw_frame=frame,
        working_frame=frame.copy()
    )
    
    # 4. Execute process
    results, errors, warnings = mock_ts_module.process(frame, context)
    
    # 5. Verify results
    assert len(errors) == 0
    assert len(warnings) == 0
    assert results["status"] == "Active"
    
    # Verify counts (Note: box5 is outside upper 45% ROI of 480px, so it's ignored)
    assert results["red_count"] == 1
    assert results["green_count"] == 1
    assert results["yellow_count"] == 1
    assert results["unknown_count"] == 1
    
    # Verify context metadata standardized schema
    assert "traffic_signal_detection" in context.metadata
    ts_data = context.metadata["traffic_signal_detection"]
    
    # Signal IDs are sorted horizontally (by x1 coordinate):
    # Box 1 (x1=100) -> ID 1 (Red)
    # Box 4 (x1=200) -> ID 2 (Unknown)
    # Box 2 (x1=300) -> ID 3 (Green)
    # Box 3 (x1=500) -> ID 4 (Yellow)
    assert len(ts_data) == 4
    
    assert ts_data[1]["status"] == "Red"
    assert ts_data[1]["module_name"] == "traffic_signal_detection"
    assert ts_data[1]["tracking_id"] == -1
    assert ts_data[1]["vehicle_class"] == -1
    assert ts_data[1]["confidence"] == 0.98
    
    assert ts_data[2]["status"] == "Unknown"
    assert ts_data[2]["confidence"] == 0.85
    
    assert ts_data[3]["status"] == "Green"
    assert ts_data[3]["confidence"] == 0.95
    
    assert ts_data[4]["status"] == "Yellow"
    assert ts_data[4]["confidence"] == 0.90
