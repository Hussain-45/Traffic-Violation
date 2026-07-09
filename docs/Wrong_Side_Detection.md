# Wrong Side Detection Module

The **Wrong Side Detection Module** evaluates vehicle trajectories to determine if tracked objects are traveling against the permitted lane direction.

---

## 1. Architecture

The module utilizes three centralized shared services to make its decisions without duplicate geometry or trajectory calculations:

```
            TrajectoryService ─────────┐
                   │                   │
                   ▼                   ▼
              MotionState ────► Wrong Side Detection ◄──── RoadSceneService
                                       │
                                       ▼
                              Standard DetectionResult
```

- **[trajectory_service.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/services/trajectory_service.py)** — Feeds vehicle coordinate centers from active ByteTrack trackers on every frame.
- **[motion_state.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/shared/schemas/motion_state.py)** — Encapsulates cumulative vectors, velocities, heading angles, track ages, and displacement values.
- **[road_scene_service.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/services/road_scene_service.py)** — Acts as the single source of truth for intersection borders, active lane orientations, and permitted flow angles.

---

## 2. Motion Analysis & Expected Flow

Permitted flow heading directions are resolved by comparing the vehicle's heading vector angle with the expected lane heading angle from `RoadSceneService`:

- **Expected Flow Angle**: Default flow is downward towards the camera (angle `90.0` degrees).
- **Heading Calculation**:
  $$\theta = \arctan2(dy, dx)$$
- **Displacement Check**:
  $$\text{displacement} = \sqrt{dx^2 + dy^2}$$

---

## 3. Temporal Validation & Confirmation Buffers

To prevent transient track jitter from triggering false violations, the module applies strict temporal gates:

1. **Gate Criteria**:
   - `track_age >= minimum_track_age` (default: 10 frames)
   - `total_distance >= minimum_distance` (default: 30.0 pixels)
   - `history_length >= minimum_history` (default: 5 coordinates)
   - `confidence >= minimum_motion_confidence` (default: 0.70)
2. **Consecutive Confirmation Smoothing**:
   - Classifications must occur consistently for `consecutive_confirmations` (default: 3 frames) before the vehicle's stable state transitions to `"Wrong Side"`.

---

## 4. Standardized Output Schema

Output results are exported using the shared `DetectionResult` Pydantic schema:

```json
{
  "module_name": "wrong_side_detection",
  "tracking_id": 4,
  "vehicle_class": 2,
  "region": [250.0, 400.0, 350.0, 520.0],
  "status": "Wrong Side",
  "confidence": 0.92,
  "timestamp": 1783584852.18,
  "frame_id": 1092,
  "metadata": {
    "travel_angle": 270.0,
    "stable_confirmations": 4
  }
}
```

---

## 5. Pipeline Configuration

Values are stored in [pipeline.yaml](file:///c:/Users/samee/Desktop/Traffic%20Violation/configs/pipeline.yaml):

```yaml
  wrong_side_detection:
    enabled: true
    confidence_threshold: 0.50
    minimum_track_age: 10
    minimum_distance: 30.0
    minimum_angle_difference: 135.0
    minimum_history: 5
    minimum_motion_confidence: 0.70
    consecutive_confirmations: 3
```

---

## 6. Future Improvements

1. **Multi-Lane Geometry mapping**: Map multiple distinct lane polygons with individual flow orientation angles using camera perspective calibration matrices.
2. **U-Turn Detection**: Track progressive heading changes from $90^\circ \to 270^\circ$ inside intersection ROIs to differentiate wrong side travel from legal/illegal U-turns.
