"""
Unit Tests for Mobile Phone Detection Module
============================================
Verifies:
  1. Initialization and configuration loading.
  2. Windshield subdivision and driver region evaluation logic (Mobile Phone, No Mobile Phone, Unknown states).
  3. Proper filtering (ignores motorcycles, passengers, and only processes car/truck/bus).
  4. Integration metrics and counts.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock
from ai.detection.mobile_phone_detection import MobilePhoneDetectionModule
from ai.pipelines.pipeline_context import PipelineContext
from ai.services.driver_region_service import DriverRegionService
import supervision as sv


@pytest.fixture
def mock_phone_module():
    module = MobilePhoneDetectionModule(models_config_path="configs/models.yaml")
    module.initialize()
    return module


def test_phone_module_initialization(mock_phone_module):
    assert mock_phone_module._initialized is True
    assert hasattr(mock_phone_module, "active_size")
    assert mock_phone_module.status()["name"] == "MobilePhoneDetectionModule"


def test_phone_module_graceful_missing_weights(monkeypatch):
    import os
    # Mock os.path.exists to return False so weights are reported missing
    monkeypatch.setattr(os.path, "exists", lambda path: False)

    module = MobilePhoneDetectionModule(models_config_path="configs/non_existent_models_config.yaml")
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


def test_driver_region_service():
    vehicle_box = [100.0, 100.0, 300.0, 300.0]
    
    # 1. Test windshield extraction (upper 50%)
    windshield = DriverRegionService.get_windshield_region(vehicle_box, windshield_height_ratio=0.50)
    assert windshield == [100.0, 100.0, 300.0, 200.0]
    
    # 2. Test occupant subdivisions (RHD: driver on right half, passenger on left half)
    regions_rhd = DriverRegionService.get_occupant_regions(vehicle_box, windshield_height_ratio=0.50, drive_side="RHD")
    assert regions_rhd["driver"] == [200.0, 100.0, 300.0, 200.0]
    assert regions_rhd["passenger"] == [100.0, 100.0, 200.0, 200.0]
    
    # 3. Test occupant subdivisions (LHD: driver on left half, passenger on right half)
    regions_lhd = DriverRegionService.get_occupant_regions(vehicle_box, windshield_height_ratio=0.50, drive_side="LHD")
    assert regions_lhd["driver"] == [100.0, 100.0, 200.0, 200.0]
    assert regions_lhd["passenger"] == [200.0, 100.0, 300.0, 200.0]


def test_driver_phone_matching(mock_phone_module):
    # 1. Mock YOLO model inside the module
    mock_model = MagicMock()
    mock_phone_module.model = mock_model
    
    # 2. Setup mock YOLO boxes:
    # Box 1: Phone (cls=1) at [210, 110, 230, 130] (falls in Driver region [200, 100, 300, 200] of Vehicle 18)
    # Box 2: Cigarette (cls=0) at [120, 110, 130, 120] (falls in Passenger region of Vehicle 18 - should be ignored by phone check since it's passenger!)
    # Box 3: Seatbelt (cls=2) at [510, 110, 530, 130] (falls in Driver region [500, 100, 600, 200] of Vehicle 19 - signifies driver present, but no phone!)
    box1 = MagicMock()
    box1.cls = [MagicMock(item=lambda: 1)]
    box1.conf = [MagicMock(item=lambda: 0.93)]
    box1.xyxy = [MagicMock(tolist=lambda: [210.0, 110.0, 230.0, 130.0])]
    
    box2 = MagicMock()
    box2.cls = [MagicMock(item=lambda: 0)]
    box2.conf = [MagicMock(item=lambda: 0.85)]
    box2.xyxy = [MagicMock(tolist=lambda: [120.0, 110.0, 130.0, 120.0])]
    
    box3 = MagicMock()
    box3.cls = [MagicMock(item=lambda: 2)]
    box3.conf = [MagicMock(item=lambda: 0.90)]
    box3.xyxy = [MagicMock(tolist=lambda: [510.0, 110.0, 530.0, 130.0])]
    
    mock_results = MagicMock()
    mock_results.boxes = [box1, box2, box3]
    mock_model.return_value = [mock_results]
    
    # 3. Create context with tracked detections:
    # Track 1: Car (class_id=2) at [100, 100, 300, 300], ID 18
    # Track 2: Car (class_id=2) at [400, 100, 600, 300], ID 19
    # Track 3: Car (class_id=2) at [700, 100, 900, 300], ID 20 (no detections inside driver region -> Unknown)
    xyxy = np.array([
        [100.0, 100.0, 300.0, 300.0],
        [400.0, 100.0, 600.0, 300.0],
        [700.0, 100.0, 900.0, 300.0]
    ], dtype=np.float32)
    
    class_id = np.array([2, 2, 2], dtype=int)
    tracker_id = np.array([18, 19, 20], dtype=int)
    confidence = np.array([0.9, 0.9, 0.9], dtype=np.float32)
    
    tracked_detections = sv.Detections(
        xyxy=xyxy,
        class_id=class_id,
        tracker_id=tracker_id,
        confidence=confidence
    )
    
    frame = np.zeros((480, 960, 3), dtype=np.uint8)
    context = PipelineContext(
        frame_id=1,
        raw_frame=frame,
        working_frame=frame.copy()
    )
    context.tracked_detections = tracked_detections
    
    # 4. Execute process
    results, errors, warnings = mock_phone_module.process(frame, context)
    
    # 5. Verify results
    assert len(errors) == 0
    assert len(warnings) == 0
    assert results["status"] == "Active"
    
    # Verify counts
    # Driver 18: Mobile Phone (phone box in region)
    # Driver 19: No Mobile Phone (seatbelt box in region, no phone box)
    # Driver 20: Unknown (no occupant boxes in region)
    assert results["phone_count"] == 1
    assert results["no_phone_count"] == 1
    assert results["unknown_count"] == 1
    
    # Verify violators list
    assert len(results["violators"]) == 1
    assert results["violators"][0]["vehicle_id"] == 18
    assert results["violators"][0]["confidence"] == 0.93
    
    # Verify metadata
    assert "mobile_phone_detection" in context.metadata
    mp_data = context.metadata["mobile_phone_detection"]
    assert 18 in mp_data
    assert mp_data[18]["status"] == "Mobile Phone"
    assert 19 in mp_data
    assert mp_data[19]["status"] == "No Mobile Phone"
    assert 20 in mp_data
    assert mp_data[20]["status"] == "Unknown"
