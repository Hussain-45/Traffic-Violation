# MotionState & TrajectoryService Architecture

The **MotionState** model and updated **TrajectoryService** centralize and standardize all vehicle motion evaluation, vector arithmetic, velocity estimation, acceleration tracking, and coordinate predictions in the Traffic Violation AI pipeline.

---

## 1. Purpose & Architecture

Downstream violation modules (such as Wrong Side Detection, Stop Line Crossing, Lane Departure, and Speed Estimation) must not calculate vectors or average coordinates individually. Instead, they rely on a single, shared, strongly-typed **MotionState** object returned by the Trajectory Service.

```
                  ┌───────────────────────┐
                  │   Tracking Service    │  (ByteTrack IDs)
                  └───────────┬───────────┘
                              │
                  ┌───────────▼───────────┐
                  │   TrajectoryService   │  (Accumulates bounding boxes)
                  └───────────┬───────────┘
                              │
                  ┌───────────▼───────────┐
                  │      MotionState      │  (Strongly-typed Pydantic model)
                  └─────┬───────────┬─────┘
                        │           │
       ┌────────────────▼─┐       ┌─▼────────────────┐
       │ Wrong Side Det.  │       │  Stop Line Cross │  (Step 13)
       └──────────────────┘       └──────────────────┘
```

---

## 2. Model Schema

Defined in [motion_state.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/shared/schemas/motion_state.py):

### Position Model
Used to represent an annotated coordinate center:
- `x` (float): X-coordinate center.
- `y` (float): Y-coordinate center.
- `timestamp` (float): Evaluation epoch.
- `frame_id` (int, optional): Numeric index of the frame.

### MotionState Model
- `tracking_id` (int): Unique tracking ID of the vehicle.
- `current_position` (Position): Last recorded center.
- `previous_position` (Position, optional): Second-to-last center.
- `motion_vector` (List[float]): Cumulative displacement vector `[dx, dy]` from the start of track history.
- `normalized_direction` (List[float]): Unit vector `[ndx, ndy]` for direction analysis.
- `travel_angle` (float, optional): Direction heading angle in degrees (0 to 360).
- `average_velocity` (float): Average displacement velocity in pixels/second.
- `instantaneous_velocity` (float): Speed between the last two positions.
- `acceleration` (float): Rate of velocity change in pixels/second².
- `total_distance` (float): Sum of segment lengths along the track path.
- `history_length` (int): Number of coordinate updates currently stored.
- `track_age` (int): Number of frames processed since vehicle initialization.
- `predicted_position` (Position, optional): Linear projection for the next position.
- `timestamp` (float): Current timestamp.
- `metadata` (dict): Module-specific attributes.

---

## 3. Caching & Performance

To guarantee **O(1)** retrieval latency, `TrajectoryService` automatically re-evaluates the vehicle's motion metrics and caches the result inside `self.motion_cache` immediately upon calling `update_trajectory()`.

Subsequent calls to:
```python
state = trajectory_service.get_motion_state(tracking_id)
```
retrieve the cached `MotionState` instantly, avoiding duplicate trigonometry or distance computations during downstream execution.

---

## 4. Usage Example

### Updating Vehicle Motion
```python
# During tracking phase
trajectory_service.update_trajectory(
    vehicle_id=track_id,
    bbox_xyxy=vehicle_box,
    timestamp=current_time
)
```

### Downstream Consumption
```python
state = trajectory_service.get_motion_state(track_id)

# Check direction
if state.motion_vector[1] < 0:
    logger.info("Vehicle is moving away from the camera.")

# Check heading angle
if state.travel_angle is not None and 180 < state.travel_angle < 360:
    logger.warning("Vehicle heading contradicts lane orientation!")
```

---

## 5. Backward Compatibility

All existing methods remain fully supported and delegate internally to the cached `MotionState` parameters:
- `get_trajectory(vehicle_id)`
- `get_motion_vector(vehicle_id)`
- `get_heading_angle(vehicle_id)`
- `get_motion_classification(vehicle_id)`
- `clean_inactive_ids(active_ids)`
