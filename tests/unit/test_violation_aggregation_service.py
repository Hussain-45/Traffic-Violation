"""
Unit Tests for ViolationAggregationService
==========================================
Verifies:
  1. Context creation and clean initialization.
  2. Individual module updates (helmet, seatbelt, phone, wrong side, signal, triple riding).
  3. Temporal and confidence aggregation logic.
  4. Duplicate suppression on the same frame.
  5. Timeout and stale context cleanup.
  6. Statistics calculation correctness.
  7. Performance & scale testing (100+ tracked vehicles).
"""
import pytest
import numpy as np
from unittest.mock import MagicMock

from ai.services.violation_aggregation_service import ViolationAggregationService
from ai.pipelines.pipeline_context import PipelineContext


@pytest.fixture
def clean_service():
    service = ViolationAggregationService()
    service.reset()
    return service


def test_service_initialization(clean_service):
    assert clean_service.contexts == {}
    assert clean_service.history_length == 20
    assert clean_service.context_timeout == 5.0
    assert clean_service.get_statistics()["total_tracked"] == 0


def test_update_detection_creates_context(clean_service):
    clean_service.update_detection(
        tracking_id=5,
        module_name="helmet_detection",
        status="No Helmet",
        confidence=0.85,
        timestamp=100.0,
        frame_id=1
    )

    ctx = clean_service.get_context(5)
    assert ctx is not None
    assert ctx.tracking_id == 5
    assert ctx.helmet_status == "No Helmet"
    assert ctx.helmet_confidence == 0.85
    assert ctx.timestamp == 100.0
    assert ctx.frame_id == 1

    # Verify history entry created for No Helmet (which is a violation status)
    assert len(ctx.violation_history) == 1
    assert ctx.violation_history[0].module_name == "helmet_detection"
    assert ctx.violation_history[0].status == "No Helmet"


def test_update_detection_normal_ignores_violation_history(clean_service):
    clean_service.update_detection(
        tracking_id=6,
        module_name="helmet_detection",
        status="Helmet",
        confidence=0.95,
        timestamp=100.0,
        frame_id=1
    )

    ctx = clean_service.get_context(6)
    assert ctx is not None
    assert ctx.helmet_status == "Helmet"
    # No violation history entries for compliant state
    assert len(ctx.violation_history) == 0


def test_confidence_and_verification_states(clean_service):
    # Update No Helmet, but frame count is 1 (minimum_frames is 3)
    clean_service.update_detection(
        tracking_id=7,
        module_name="helmet_detection",
        status="No Helmet",
        confidence=0.90,
        timestamp=100.0,
        frame_id=1
    )
    ctx = clean_service.get_context(7)
    assert ctx.verification_state == "Processing"
    assert ctx.evidence_ready is False

    # Simulate next 2 frames
    clean_service.update_detection(7, "helmet_detection", "No Helmet", 0.90, 100.1, 2)
    clean_service.update_detection(7, "helmet_detection", "No Helmet", 0.90, 100.2, 3)

    # Frame count is now >= 3 (minimum_frames) and confidence >= 0.50
    assert ctx.verification_state == "Verified"
    assert ctx.evidence_ready is True
    assert ctx.stable_detection is True


def test_duplicate_frame_suppression(clean_service):
    # Two updates for same vehicle, same module, same frame ID
    clean_service.update_detection(8, "wrong_side_detection", "Wrong Side", 0.88, 100.0, 1)
    clean_service.update_detection(8, "wrong_side_detection", "Wrong Side", 0.88, 100.0, 1)

    ctx = clean_service.get_context(8)
    assert ctx.frame_count == 1
    assert len(ctx.violation_history) == 1  # No duplicate history entries


def test_context_timeout_cleanup(clean_service):
    # Add active vehicle
    clean_service.update_detection(9, "phone_detection", "Mobile Phone", 0.82, 100.0, 1)
    assert clean_service.get_context(9) is not None

    # Trigger cleanup with current timestamp inside timeout bounds
    clean_service.cleanup_stale_contexts(104.0)
    assert clean_service.get_context(9) is not None

    # Trigger cleanup with timestamp past timeout limit (timeout is 5.0)
    clean_service.cleanup_stale_contexts(106.0)
    assert clean_service.get_context(9) is None


def test_statistics_aggregation(clean_service):
    clean_service.update_detection(10, "helmet_detection", "No Helmet", 0.90, 100.0, 1)
    clean_service.update_detection(11, "phone_detection", "Mobile Phone", 0.85, 100.0, 1)
    clean_service.update_detection(12, "wrong_side_detection", "Wrong Side", 0.95, 100.0, 1)

    stats = clean_service.get_statistics()
    assert stats["total_tracked"] == 3
    assert stats["violations_breakdown"]["no_helmet"] == 1
    assert stats["violations_breakdown"]["phone_usage"] == 1
    assert stats["violations_breakdown"]["wrong_side"] == 1
    assert stats["violations_breakdown"]["red_light_jump"] == 0


def test_scale_and_performance(clean_service):
    import time
    start_time = time.time()

    # Feed 100 tracked vehicles
    for i in range(100):
        clean_service.update_detection(
            tracking_id=1000 + i,
            module_name="seat_belt_detection",
            status="No Seat Belt",
            confidence=0.75,
            timestamp=200.0,
            frame_id=500
        )

    end_time = time.time()
    duration = end_time - start_time
    
    # Needs to be extremely fast (O(1) lookups)
    assert duration < 0.10  # 100 context insertions in less than 100ms
    assert len(clean_service.get_all_contexts()) == 100
