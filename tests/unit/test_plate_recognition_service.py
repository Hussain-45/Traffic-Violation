"""
Unit Tests for Plate Recognition Service
========================================
Verifies:
  1. Text normalization and Indian registration OCR confusion corrections.
  2. Regex validation rules (Valid, Possibly Valid, Invalid).
  3. Multi-frame voting and stable plate promotion.
  4. Aggregated confidence metrics calculation.
  5. Scalability performance (500 OCR updates).
"""
import pytest
import time
from loguru import logger

from ai.services.plate_recognition_service import plate_recognition_service


@pytest.fixture(autouse=True)
def clean_service():
    plate_recognition_service.reset()
    yield


def test_normalization_confusions():
    # Test State Code (letters: O -> 0 should not happen. It should convert 0 -> O)
    assert plate_recognition_service.normalize_plate("0h12ab1234") == "OH12AB1234"
    # Test District Code (digits: O -> 0)
    assert plate_recognition_service.normalize_plate("mhO2ab1234") == "MH02AB1234"
    # Test Series (letters: 1 -> I)
    assert plate_recognition_service.normalize_plate("mh12a11234") == "MH12AI1234"
    # Test Reg Code (digits: O -> 0, I -> 1)
    assert plate_recognition_service.normalize_plate("mh12ab12O3") == "MH12AB1203"
    assert plate_recognition_service.normalize_plate("mh12ab12I4") == "MH12AB1214"


def test_plate_validation():
    # Standard format: MH12AB1234 and MH12A1234 (1 or 2 series letters)
    assert plate_recognition_service.validate_plate("MH12AB1234") == "Valid"
    assert plate_recognition_service.validate_plate("MH12A1234") == "Valid"
    # Loose format: MH121234
    assert plate_recognition_service.validate_plate("MH121234") == "Possibly Valid"
    # Bad format
    assert plate_recognition_service.validate_plate("XYZ") == "Invalid"


def test_multi_frame_voting():
    v_id = 99
    
    # 1st frame: MH12AB1234 (conf 0.8)
    plate_recognition_service.process_ocr_result(
        vehicle_id=v_id,
        recognized_text="mh12ab1234",
        confidence=0.80,
        engine_name="mock_ocr",
        timestamp=100.0,
        frame_id=1
    )
    
    # Not stable yet (votes = 1 < 3)
    assert plate_recognition_service.get_stable_plate(v_id) is None
    
    # 2nd frame: MH12AB1234 (conf 0.85)
    plate_recognition_service.process_ocr_result(
        vehicle_id=v_id,
        recognized_text="mh12ab1234",
        confidence=0.85,
        engine_name="mock_ocr",
        timestamp=101.0,
        frame_id=2
    )
    
    # 3rd frame: Conflicting read MH12AB1235 (conf 0.90)
    plate_recognition_service.process_ocr_result(
        vehicle_id=v_id,
        recognized_text="mh12ab1235",
        confidence=0.90,
        engine_name="mock_ocr",
        timestamp=102.0,
        frame_id=3
    )
    
    # 4th frame: MH12AB1234 (conf 0.90) - now has 3 votes
    plate_recognition_service.process_ocr_result(
        vehicle_id=v_id,
        recognized_text="mh12ab1234",
        confidence=0.90,
        engine_name="mock_ocr",
        timestamp=103.0,
        frame_id=4
    )

    # Winner is MH12AB1234 with 3 votes
    assert plate_recognition_service.get_stable_plate(v_id) == "MH12AB1234"
    state = plate_recognition_service.get_recognition_state(v_id)
    assert state.vote_count == 3
    assert state.validation_status == "Valid"
    # Average confidence: (0.8 + 0.85 + 0.9) / 3 = 0.85
    assert abs(state.aggregated_confidence - 0.85) < 0.01


def test_plate_recognition_performance():
    start_time = time.perf_counter()
    
    for i in range(500):
        v_id = i % 10  # 10 vehicles getting 50 reads each
        plate_recognition_service.process_ocr_result(
            vehicle_id=v_id,
            recognized_text=f"mh12ab123{v_id}",
            confidence=0.85,
            engine_name="mock_ocr",
            timestamp=200.0 + i,
            frame_id=i
        )
        
    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000.0
    logger.info(f"Recognition performance for 500 updates: {elapsed_ms:.2f}ms")
    
    # Must process 500 updates in less than 200ms
    assert elapsed_ms < 200.0
    assert plate_recognition_service.get_stable_plate(3) == "MH12AB1233"
