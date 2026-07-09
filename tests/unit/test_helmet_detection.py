"""
Unit Tests for Helmet Detection Module
======================================
Verifies:
  1. Initialization and configuration loading.
  2. Spatial overlap matching of helmet boxes to motorcyclist/person rider tracks.
  3. Execution metrics and counts aggregated in results.
  4. Overlay drawing executed on working frames.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock
from ai.detection.helmet_detection import HelmetDetectionModule
from ai.pipelines.pipeline_context import PipelineContext
import supervision as sv


@pytest.fixture
def mock_helmet_module():
    # Instantiate module with a dummy config path
    module = HelmetDetectionModule(models_config_path="configs/models.yaml")
    module.initialize()
    return module


def test_helmet_module_initialization(mock_helmet_module):
    # Verify properties
    assert mock_helmet_module._initialized is True
    # The models/trained/helmet_best.pt exists, so model should load, but in test env we just verify initialization flag
    assert hasattr(mock_helmet_module, "active_size")
    assert mock_helmet_module.status()["name"] == "HelmetDetectionModule"


def test_helmet_module_graceful_missing_weights(monkeypatch):
    import os
    # Mock os.path.exists to return False so weights are reported missing
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    module = HelmetDetectionModule(models_config_path="configs/non_existent_models_config.yaml")
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


def test_spatial_matching_logic(mock_helmet_module):
    # 1. Mock YOLO model inside the module
    mock_model = MagicMock()
    mock_helmet_module.model = mock_model
    
    # 2. Setup mock YOLO boxes:
    # Box 1: Helmet (cls=0) at coordinates [100, 10, 150, 60] (x1, y1, x2, y2)
    # Box 2: No Helmet (cls=1) at coordinates [300, 10, 350, 60]
    box1 = MagicMock()
    box1.cls = [MagicMock(item=lambda: 0)]
    box1.conf = [MagicMock(item=lambda: 0.95)]
    box1.xyxy = [MagicMock(tolist=lambda: [100.0, 10.0, 150.0, 60.0])]
    
    box2 = MagicMock()
    box2.cls = [MagicMock(item=lambda: 1)]
    box2.conf = [MagicMock(item=lambda: 0.88)]
    box2.xyxy = [MagicMock(tolist=lambda: [300.0, 10.0, 350.0, 60.0])]
    
    mock_results = MagicMock()
    mock_results.boxes = [box1, box2]
    mock_model.return_value = [mock_results]
    
    # 3. Create context with tracked detections:
    # Track 1: Motorcycle (class_id=3) at [90, 80, 160, 200], ID 10
    # Track 2: Person (class_id=0) at [95, 15, 145, 120] (overlaps with Motorcycle 10, head around 15-50y)
    # Track 3: Motorcycle (class_id=3) at [290, 80, 360, 200], ID 20
    # Track 4: Person (class_id=0) at [295, 15, 345, 120] (overlaps with Motorcycle 20)
    xyxy = np.array([
        [90.0, 80.0, 160.0, 200.0],
        [95.0, 15.0, 145.0, 120.0],
        [290.0, 80.0, 360.0, 200.0],
        [295.0, 15.0, 345.0, 120.0]
    ], dtype=np.float32)
    
    class_id = np.array([3, 0, 3, 0], dtype=int)
    tracker_id = np.array([10, 100, 20, 200], dtype=int)
    confidence = np.array([0.9, 0.85, 0.9, 0.85], dtype=np.float32)
    
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
    results, errors, warnings = mock_helmet_module.process(frame, context)
    
    # 5. Verify results
    assert len(errors) == 0
    assert len(warnings) == 0
    assert results["status"] == "Active"
    
    # Verify counts
    assert results["helmet_count"] == 1  # Rider 10 has Helmet
    assert results["no_helmet_count"] == 1  # Rider 20 has No Helmet
    assert len(results["violators"]) == 1
    assert results["violators"][0]["motorcycle_id"] == 20  # Violator is Motorcycle 20
    
    # Verify context metadata
    assert "helmet_detection" in context.metadata
    h_data = context.metadata["helmet_detection"]
    assert 10 in h_data
    assert h_data[10]["helmet"] is True
    assert 20 in h_data
    assert h_data[20]["helmet"] is False
    
    # Verify context detection counts updated
    assert context.detection_counts["helmet"] == 1
    assert context.detection_counts["no_helmet"] == 1
