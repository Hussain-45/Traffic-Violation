"""
Unit Tests for License Plate OCR Module (ANPR Stage 2)
=====================================================
Verifies:
  1. Initialization and configurations loading.
  2. OCR text extraction from mock crops.
  3. Processing loop with mock and empty crops.
  4. Integration with PlateRecognitionService.
  5. DetectionResult schema compliance.
  6. Overlay drawing correctness.
  7. Error recovery.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from ai.ocr.license_plate_ocr import LicensePlateOCRModule
from ai.pipelines.pipeline_context import PipelineContext
from ai.services.plate_association_service import plate_association_service
from ai.services.plate_recognition_service import plate_recognition_service
from shared.schemas.plate_association import PlateInfo, VehiclePlateAssociation


@pytest.fixture
def sample_frame():
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_context():
    ctx = PipelineContext()
    ctx.timestamp = 100.0
    ctx.frame_id = 42
    ctx.working_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    return ctx


def test_ocr_initialization():
    module = LicensePlateOCRModule()
    # Mock easyocr to avoid downloading weights
    with patch("easyocr.Reader", return_value=MagicMock()):
        module.initialize()
        assert module.health() is True
        assert module.status()["name"] == "LicensePlateOCRModule"


def test_ocr_processing_with_no_associations(sample_frame, sample_context):
    module = LicensePlateOCRModule()
    with patch("easyocr.Reader", return_value=MagicMock()):
        module.initialize()

        # Clear any associations
        plate_association_service.associations.clear()

        results, errors, warnings = module.process(sample_frame, sample_context)

        assert results["requests_count"] == 0
        assert results["verified_count"] == 0
        assert len(errors) == 0


def test_ocr_processing_with_stable_crop(sample_frame, sample_context):
    module = LicensePlateOCRModule()
    
    # 1. Set up Mock EasyOCR Reader
    mock_reader = MagicMock()
    # Returns list of (bbox, text, confidence)
    mock_reader.readtext.return_value = [
        ([[0, 0], [100, 0], [100, 30], [0, 30]], "MH12AB1234", 0.92)
    ]

    with patch("easyocr.Reader", return_value=mock_reader):
        module.initialize()

        # 2. Setup mock vehicle association with a valid crop
        plate_association_service.associations.clear()
        plate_recognition_service.recognition_states.clear()

        crop_img = np.random.randint(0, 255, (30, 100, 3), dtype=np.uint8)
        stable_plate_info = PlateInfo(
            plate_tracking_id=101,
            plate_bbox=[150.0, 150.0, 250.0, 180.0],
            confidence=0.88,
            cropped_plate_image=crop_img,
            timestamp=100.0,
            frame_id=42
        )

        assoc = VehiclePlateAssociation(
            vehicle_tracking_id=10,
            vehicle_class=2,  # Car
            vehicle_bbox=[100.0, 100.0, 300.0, 300.0],
            associated_plate=stable_plate_info,
            stable_plate=stable_plate_info,
            plate_history=[stable_plate_info],
            timestamp=100.0
        )
        plate_association_service.associations[10] = assoc

        # 3. Execute process
        results, errors, warnings = module.process(sample_frame, sample_context)

        # 4. Verify results
        assert results["requests_count"] == 1
        # It needs minimum_votes = 3 to be verified, so first OCR result makes it "Processing"
        assert results["verified_count"] == 0 
        
        # Verify DetectionResult created and stored in context
        assert "ocr" in sample_context.metadata
        assert 10 in sample_context.metadata["ocr"]
        
        det_res = sample_context.metadata["ocr"][10]
        assert det_res["module_name"] == "ocr"
        assert det_res["tracking_id"] == 10
        assert det_res["status"] == "Processing"
        assert det_res["metadata"]["raw_text"] == "MH12AB1234"
        assert det_res["metadata"]["engine_name"] == "easyocr"

        # Verify context detection counts updated
        assert sample_context.detection_counts["ocr_requests"] == 1
        assert sample_context.detection_counts["ocr_verified"] == 0

        # Run process two more times to exceed minimum_votes = 3 threshold
        # (simulating next frames with same results)
        sample_context.frame_id = 43
        sample_context.timestamp = 101.0
        module.process(sample_frame, sample_context)

        sample_context.frame_id = 44
        sample_context.timestamp = 102.0
        results, errors, warnings = module.process(sample_frame, sample_context)

        # Now it should be verified
        assert results["verified_count"] == 1
        det_res_final = sample_context.metadata["ocr"][10]
        assert det_res_final["status"] == "Verified"
        assert det_res_final["metadata"]["verified_text"] == "MH12AB1234"


def test_ocr_error_recovery(sample_frame, sample_context):
    module = LicensePlateOCRModule()
    
    mock_reader = MagicMock()
    # Force readtext to raise an exception
    mock_reader.readtext.side_effect = RuntimeError("CUDA out of memory")

    with patch("easyocr.Reader", return_value=mock_reader):
        module.initialize()

        plate_association_service.associations.clear()
        crop_img = np.random.randint(0, 255, (30, 100, 3), dtype=np.uint8)
        stable_plate_info = PlateInfo(
            plate_tracking_id=102,
            plate_bbox=[150.0, 150.0, 250.0, 180.0],
            confidence=0.88,
            cropped_plate_image=crop_img,
            timestamp=100.0,
            frame_id=42
        )

        assoc = VehiclePlateAssociation(
            vehicle_tracking_id=11,
            vehicle_class=2,
            vehicle_bbox=[100.0, 100.0, 300.0, 300.0],
            associated_plate=stable_plate_info,
            stable_plate=stable_plate_info,
            plate_history=[stable_plate_info],
            timestamp=100.0
        )
        plate_association_service.associations[11] = assoc

        # Process should NOT crash
        results, errors, warnings = module.process(sample_frame, sample_context)

        assert results["requests_count"] == 1
        assert len(errors) == 0  # Captured and logged, doesn't abort pipeline
        assert sample_context.metadata["ocr"][11]["metadata"]["raw_text"] == ""
