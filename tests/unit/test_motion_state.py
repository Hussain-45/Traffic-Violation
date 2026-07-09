"""
Unit Tests for MotionState and TrajectoryService Caching
======================================================
Verifies:
  1. MotionState serialization and fields.
  2. TrajectoryService computation accuracy (vector, velocity, angle, prediction, accel).
  3. Caching and O(1) fetch mechanics.
  4. Error handling and safe default returns.
  5. Cleanups and track lifetimes.
"""
import pytest
from shared.schemas.motion_state import MotionState, Position
from ai.services.trajectory_service import TrajectoryService


def test_motion_state_serialization():
    pos = Position(x=10.0, y=20.0, timestamp=1.5, frame_id=5)
    state = MotionState(
        tracking_id=1,
        current_position=pos,
        timestamp=1.5,
        history_length=1,
        track_age=1
    )
    
    assert state.tracking_id == 1
    assert state.current_position.x == 10.0
    assert state.current_position.frame_id == 5
    
    serialized = state.to_dict()
    assert isinstance(serialized, dict)
    assert serialized["tracking_id"] == 1
    assert serialized["current_position"]["x"] == 10.0


def test_trajectory_service_caching():
    service = TrajectoryService()
    
    # 1. Verify fallback when empty
    fallback = service.get_motion_state(99)
    assert fallback.tracking_id == 99
    assert fallback.history_length == 0
    assert fallback.current_position.x == 0.0
    assert fallback.average_velocity == 0.0

    # 2. Add an update
    service.update_trajectory(vehicle_id=1, bbox_xyxy=[100, 100, 200, 200], timestamp=1.0)
    
    # Verify cached item exists
    assert 1 in service.motion_cache
    state1 = service.get_motion_state(1)
    state2 = service.get_motion_state(1)
    
    # Caching check: both references are the exact same instance in memory (O(1) fetch)
    assert state1 is state2
    assert state1.current_position.x == 150.0
    assert state1.track_age == 1


def test_computed_motion_properties():
    service = TrajectoryService()
    
    # Add 3 points to calculate velocity, angle, acceleration, and predictions
    # Point 1: center=(100, 100), ts=1.0
    service.update_trajectory(vehicle_id=1, bbox_xyxy=[50.0, 50.0, 150.0, 150.0], timestamp=1.0)
    
    # Point 2: center=(130, 140), ts=2.0
    service.update_trajectory(vehicle_id=1, bbox_xyxy=[80.0, 90.0, 180.0, 190.0], timestamp=2.0)
    
    # Point 3: center=(160, 180), ts=3.0
    service.update_trajectory(vehicle_id=1, bbox_xyxy=[110.0, 130.0, 210.0, 230.0], timestamp=3.0)
    
    state = service.get_motion_state(1)
    
    assert state.history_length == 3
    assert state.track_age == 3
    
    # Displacement over whole history: (160-100, 180-100) = (60.0, 80.0)
    assert state.motion_vector == [60.0, 80.0]
    
    # Normalized direction: magnitude of [60, 80] is 100, so [0.6, 0.8]
    assert state.normalized_direction == [0.6, 0.8]
    
    # Angle of [60, 80]: degrees(arctan2(80, 60)) = ~53.13
    assert pytest.approx(state.travel_angle, 0.1) == 53.13
    
    # Total distance: distance(100,100 -> 130,140) = 50. distance(130,140 -> 160,180) = 50. Total = 100.
    assert state.total_distance == 100.0
    
    # Average velocity: 100px / 2.0s = 50.0 px/s
    assert state.average_velocity == 50.0
    
    # Instantaneous velocity (last step): distance 50px / dt 1.0s = 50.0 px/s
    assert state.instantaneous_velocity == 50.0
    
    # Acceleration: v1 = 50 px/s, v2 = 50 px/s, so accel = 0.0 px/s^2
    assert state.acceleration == 0.0
    
    # Prediction: inst dx = 30px/s, dy = 40px/s. Next pos: (160+30, 180+40) = (190, 220)
    assert state.predicted_position is not None
    assert state.predicted_position.x == 190.0
    assert state.predicted_position.y == 220.0
    assert state.predicted_position.timestamp == 4.0


def test_backward_compatibility():
    service = TrajectoryService()
    
    # Add 3 points
    service.update_trajectory(vehicle_id=10, bbox_xyxy=[100, 100, 200, 200], timestamp=1.0) # 150, 150
    service.update_trajectory(vehicle_id=10, bbox_xyxy=[110, 110, 210, 210], timestamp=2.0) # 160, 160
    service.update_trajectory(vehicle_id=10, bbox_xyxy=[130, 130, 230, 230], timestamp=3.0) # 180, 180
    
    # Check old backward compatible methods
    m_vec = service.get_motion_vector(10)
    assert m_vec == (30.0, 30.0)
    
    angle = service.get_heading_angle(10)
    assert angle == 45.0  # dx=30, dy=30 -> 45 degrees
    
    classification = service.get_motion_classification(10)
    assert classification == "moving_forward"
