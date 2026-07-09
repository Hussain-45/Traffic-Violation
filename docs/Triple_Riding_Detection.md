# Triple Riding Detection Module

The **Triple Riding Detection Module** evaluates the occupant count of tracked motorcycles using associated rider structures provided by `RiderAssociationService`. It classifies single, double, and triple riding states with temporal validation.

---

## 1. Architecture

The module integrates seamlessly into the AI Pipeline downstream of tracking and occupant association:

```
            ByteTrack Tracking Output
                       │
                       ▼
            RiderAssociationService (Occupant Mapping)
                       │
                       ▼
          TripleRidingDetectionModule (Occupant Count & States)
                       │
                       ▼
            Standardized DetectionResult
```

- **[rider_association_service.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/services/rider_association_service.py)** — Feeds the motorcycle groups containing occupant lists.
- **[trajectory_service.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/services/trajectory_service.py)** — Provides tracker age data for validation gates.

---

## 2. Detection Flow & Occupant Count Evaluation

For each active motorcycle track, the module performs the following pipeline checks:

1. **Gating Checks**:
   - `confidence >= minimum_association_confidence` (default: `0.60`)
   - `group.rider_count >= minimum_visible_riders` (default: `1`)
   - `track_age >= minimum_track_age` (default: `5` frames)
   - If any gate fails, the state evaluates as `"Unknown"`.
2. **Raw State Mapping**:
   - `rider_count == 1`: `Single Rider` (🟢)
   - `rider_count == 2`: `Double Riding` (🟡)
   - `rider_count >= 3`: `Triple Riding` (🔴)
3. **Temporal confirmation smoothing**:
   - Keeps buffers tracking consecutive raw classifications for each track ID.
   - Requires `confirmation_frames` (default: `3` frames) matching the target state before updating the stable state, preventing false positives from short occlusions.

---

## 3. Standardized Output Schema

Output results are exported using the shared `DetectionResult` Pydantic schema:

```json
{
  "module_name": "triple_riding_detection",
  "tracking_id": 40,
  "vehicle_class": 3,
  "region": [100.0, 100.0, 200.0, 300.0],
  "status": "Triple Riding",
  "confidence": 0.90,
  "timestamp": 1783584852.18,
  "frame_id": 1092,
  "metadata": {
    "rider_count": 3,
    "driver_id": 1,
    "passenger_ids": [2, 3],
    "motorcycle_group_id": 40
  }
}
```

---

## 4. Configuration

Values are stored in [pipeline.yaml](file:///c:/Users/samee/Desktop/Traffic%20Violation/configs/pipeline.yaml):

```yaml
  triple_riding_detection:
    enabled: true
    confidence_threshold: 0.50
    minimum_association_confidence: 0.60
    minimum_visible_riders: 1
    minimum_track_age: 5
    confirmation_frames: 3
    maximum_riders: 2
```

---

## 5. Overlays & Visualization

Draws annotated overlays directly onto the video frame:
- **Single Rider**: Green box `(129, 185, 16)` and tag `Moto #ID: SINGLE (1 Rider)`.
- **Double Riding**: Yellow box `(16, 185, 245)` and tag `Moto #ID: DOUBLE (2 Riders)`.
- **Triple Riding**: Red box `(68, 68, 239)` and tag `Moto #ID: TRIPLE RIDING ❌ (3 Riders)`.
- **Unknown**: Gray box `(150, 150, 150)` and tag `Moto #ID: UNKNOWN`.

---

## 6. Limitations & Future Improvements

1. **Rider Occlusion**: Heavy tailgating or side-by-side motorcycles can lead to temporary overlap misassociations.
2. **Passenger Height Gating**: Add child passenger detection based on height bounding box checks relative to the driver.
