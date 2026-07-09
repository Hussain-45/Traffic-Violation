"""
Unit Tests for Trajectory Service
=================================
Verifies:
  1. Trajectory updating and coordinate centers.
  2. Max history length enforcement.
  3. Motion vector and angle calculations.
  4. Moving vs. stationary classification.
  5. Inactive track cleanup.
"""
import pytest
from ai.services.trajectory_service import TrajectoryService


@pytest.fixture
def trajectory_service():
    return TrajectoryService(max_history_len=5)


def test_trajectory_updates(trajectory_service):
    # Update track ID 1
    trajectory_service.update_trajectory(vehicle_id=1, bbox_xyxy=[10.0, 20.0, 30.0, 40.0], timestamp=1.0)
    history = trajectory_service.get_trajectory(1)
    
    # Bbox center: cx=(10+30)/2=20, cy=(20+40)/2=30
    assert len(history) == 1
    assert history[0] == (20.0, 30.0, 1.0)


def test_trajectory_max_length(trajectory_service):
    # Push 6 updates on max size 5
    for i in range(6):
        trajectory_service.update_trajectory(vehicle_id=1, bbox_xyxy=[10.0, 20.0, 30.0, 40.0], timestamp=float(i))
        
    history = trajectory_service.get_trajectory(1)
    assert len(history) == 5
    # First update (timestamp 0.0) should be discarded
    assert history[0][2] == 1.0
    assert history[-1][2] == 5.0


def test_motion_vector_and_classification(trajectory_service):
    # Vehicle moving down the screen (dy > 0)
    trajectory_service.update_trajectory(1, [100.0, 100.0, 200.0, 200.0], 1.0)  # center = 150, 150
    trajectory_service.update_trajectory(1, [100.0, 110.0, 200.0, 210.0], 2.0)  # center = 150, 160
    trajectory_service.update_trajectory(1, [100.0, 120.0, 200.0, 220.0], 3.0)  # center = 150, 170
    
    dx, dy = trajectory_service.get_motion_vector(1)
    assert dx == 0.0
    assert dy == 20.0
    
    classification = trajectory_service.get_motion_classification(1)
    assert classification == "moving_forward"
    
    # Vehicle stationary
    trajectory_service.update_trajectory(2, [100.0, 100.0, 200.0, 200.0], 1.0)
    trajectory_service.update_trajectory(2, [100.1, 100.1, 200.1, 200.1], 2.0)
    trajectory_service.update_trajectory(2, [100.2, 100.2, 200.2, 200.2], 3.0)
    
    classification2 = trajectory_service.get_motion_classification(2, motion_threshold=2.0)
    assert classification2 == "stationary"


def test_trajectory_cleanup(trajectory_service):
    trajectory_service.update_trajectory(1, [10, 10, 20, 20], 1.0)
    trajectory_service.update_trajectory(2, [30, 30, 40, 40], 1.0)
    
    # Cleanup inactive tracks (track 2 is active, track 1 is inactive)
    trajectory_service.clean_inactive_ids(active_ids=[2])
    
    assert len(trajectory_service.get_trajectory(1)) == 0
    assert len(trajectory_service.get_trajectory(2)) == 1
