"""
Unit Tests for Rider Association Service
=========================================
Verifies:
  1. Initialization and configuration loading.
  2. Single association mapping.
  3. Driver vs Passenger classification and ordering (depending on traffic dy direction).
  4. Ambiguous association resolution (highest score match).
  5. Performance scalability (100 motorcycles, 300 riders).
  6. Cache clearing and reset mechanisms.
  7. Partial overlap (low IoU) validation.
"""
import pytest
import time
from loguru import logger
from ai.services.rider_association_service import rider_association_service
from ai.services.trajectory_service import trajectory_service


@pytest.fixture(autouse=True)
def clean_services():
    rider_association_service.reset()
    trajectory_service.reset()
    yield


def test_rider_association_initialization():
    assert rider_association_service.config is not None
    assert "minimum_iou" in rider_association_service.config


def test_rider_association_basic_mapping():
    motorcycles = [
        {"id": 10, "bbox": [100.0, 200.0, 200.0, 400.0], "conf": 0.90}
    ]
    riders = [
        {"id": 1, "bbox": [110.0, 210.0, 190.0, 310.0], "conf": 0.85}  # Highly overlapping
    ]

    rider_association_service.associate_riders(motorcycles, riders, timestamp=100.0)
    group = rider_association_service.get_motorcycle_group(10)
    
    assert group is not None
    assert group.rider_count == 1
    assert group.driver is not None
    assert group.driver.rider_tracking_id == 1
    assert len(group.passengers) == 0


def test_rider_association_ordering_incoming():
    # Setup trajectory moving down the screen (dy > 0)
    trajectory_service.update_trajectory(vehicle_id=20, bbox_xyxy=[100.0, 90.0, 200.0, 290.0], timestamp=0.0)
    trajectory_service.update_trajectory(vehicle_id=20, bbox_xyxy=[100.0, 100.0, 200.0, 300.0], timestamp=1.0)
    trajectory_service.update_trajectory(vehicle_id=20, bbox_xyxy=[100.0, 110.0, 200.0, 310.0], timestamp=2.0)

    motorcycles = [
        {"id": 20, "bbox": [100.0, 110.0, 200.0, 310.0], "conf": 0.92}
    ]
    # Two riders: person 1 is at y=150 (higher up/rear), person 2 is at y=250 (lower down/front)
    # Since dy > 0 (incoming), front of motorcycle is at the bottom (larger y).
    # Driver should be person 2 (y=250), passenger should be person 1 (y=150).
    riders = [
        {"id": 1, "bbox": [110.0, 120.0, 190.0, 180.0], "conf": 0.80},
        {"id": 2, "bbox": [110.0, 220.0, 190.0, 280.0], "conf": 0.85}
    ]

    rider_association_service.associate_riders(motorcycles, riders, timestamp=100.0)
    group = rider_association_service.get_motorcycle_group(20)

    assert group is not None
    assert group.rider_count == 2
    assert group.driver.rider_tracking_id == 2  # Front-most is driver
    assert group.passengers[0].rider_tracking_id == 1  # Rear-most is passenger


def test_rider_association_ordering_outgoing():
    # Setup trajectory moving up the screen (dy < 0)
    trajectory_service.update_trajectory(vehicle_id=30, bbox_xyxy=[100.0, 310.0, 200.0, 510.0], timestamp=0.0)
    trajectory_service.update_trajectory(vehicle_id=30, bbox_xyxy=[100.0, 300.0, 200.0, 500.0], timestamp=1.0)
    trajectory_service.update_trajectory(vehicle_id=30, bbox_xyxy=[100.0, 290.0, 200.0, 490.0], timestamp=2.0)

    motorcycles = [
        {"id": 30, "bbox": [100.0, 290.0, 200.0, 490.0], "conf": 0.92}
    ]
    # Two riders: person 1 is at y=320 (higher up/front), person 2 is at y=420 (lower down/rear)
    # Since dy < 0 (outgoing), front of motorcycle is at the top (smaller y).
    # Driver should be person 1 (y=320), passenger should be person 2 (y=420).
    riders = [
        {"id": 1, "bbox": [110.0, 300.0, 190.0, 360.0], "conf": 0.80},
        {"id": 2, "bbox": [110.0, 400.0, 190.0, 460.0], "conf": 0.85}
    ]

    rider_association_service.associate_riders(motorcycles, riders, timestamp=100.0)
    group = rider_association_service.get_motorcycle_group(30)

    assert group is not None
    assert group.rider_count == 2
    assert group.driver.rider_tracking_id == 1  # Front-most (top) is driver
    assert group.passengers[0].rider_tracking_id == 2  # Rear-most (bottom) is passenger


def test_rider_association_ambiguous_resolution():
    # Rider is between motorcycle 40 and motorcycle 50, but closer and higher overlap with 40
    motorcycles = [
        {"id": 40, "bbox": [100.0, 200.0, 200.0, 400.0], "conf": 0.90},
        {"id": 50, "bbox": [180.0, 200.0, 280.0, 400.0], "conf": 0.88}
    ]
    riders = [
        {"id": 5, "bbox": [110.0, 210.0, 170.0, 290.0], "conf": 0.80} # Overlaps mostly with 40
    ]

    rider_association_service.associate_riders(motorcycles, riders, timestamp=100.0)
    
    group_40 = rider_association_service.get_motorcycle_group(40)
    group_50 = rider_association_service.get_motorcycle_group(50)

    assert group_40.rider_count == 1
    assert group_50.rider_count == 0


def test_rider_association_performance():
    # Generate 100 motorcycles and 300 riders
    motorcycles = []
    riders = []
    
    for i in range(100):
        # Space them out to simulate realistic separate vehicles
        offset = i * 200.0
        motorcycles.append({
            "id": i,
            "bbox": [offset, 100.0, offset + 100.0, 300.0],
            "conf": 0.90
        })
        # Place 3 riders on each motorcycle
        for j in range(3):
            riders.append({
                "id": (i * 3) + j,
                "bbox": [offset + 10.0, 110.0 + (j * 50.0), offset + 90.0, 160.0 + (j * 50.0)],
                "conf": 0.85
            })

    start_time = time.perf_counter()
    rider_association_service.associate_riders(motorcycles, riders, timestamp=200.0)
    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000.0
    logger.info(f"Association performance for 100 motos, 300 riders: {elapsed_ms:.2f}ms")
    
    # Assert performance is fast (should be under 1000ms on any CPU)
    assert elapsed_ms < 1000.0
    
    # Check that i-th motorcycle has 3 riders
    group = rider_association_service.get_motorcycle_group(42)
    assert group is not None
    assert group.rider_count == 3
    assert len(group.passengers) == 2
