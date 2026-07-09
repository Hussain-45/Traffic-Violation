# Rider Association Service

The **Rider Association Service** is a central shared layer responsible for matching motorcycle detections with associated riders (people). It resolves driver and passenger roles based on relative layout and spatial movement without making final violation decisions.

---

## 1. Architecture

The service acts as a standard shared utility positioned in the pipeline execution flow directly below ByteTrack tracking updates:

```
            ByteTrack Tracking Output
                       │
                       ▼
            RiderAssociationService ◄──── TrajectoryService (Heading Vectors)
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
    Helmet Detection     Triple Riding Detection (Downstream)
```

By providing a single source of truth, it prevents downstream modules from implementing redundant matching calculations.

---

## 2. Shared Models

### `RiderInfo`
Represents an individual occupant on the motorcycle:
- `rider_tracking_id` (`int`): Person's tracker ID.
- `rider_type` (`str`): Classification role (`"driver"`, `"passenger"`, or `"unknown"`).
- `bounding_box` (`List[float]`): Rider box coordinates `[x1, y1, x2, y2]`.
- `confidence` (`float`): Detection confidence.
- `helmet_status` (`Optional[str]`): Evaluated helmet condition.
- `position_index` (`int`): Ordering order from front-to-back (0 = driver/front).

### `MotorcycleGroup`
Represents the motorcycle and all of its associated occupants:
- `motorcycle_tracking_id` (`int`): Motorcycle tracker ID.
- `motorcycle_bbox` (`List[float]`): Motorcycle box coordinates.
- `driver` (`Optional[RiderInfo]`): Identified driver (closest to the front).
- `passengers` (`List[RiderInfo]`): Sorted passenger occupants sitting behind the driver.
- `rider_count` (`int`): Total count of associated occupants.
- `confidence` (`float`): Motorcycle confidence.
- `timestamp` (`float`): Current frame evaluation timestamp.

---

## 3. Association Flow & Scoring Logic

1. **Overlap Evaluation**: For each person candidate, the service calculates the intersection ratio relative to the person's bounding box:
   $$\text{overlap\_ratio} = \frac{\text{Area}(\text{Intersection}(R, M))}{\text{Area}(R)}$$
2. **Center Distance**: Resolves Euclidean distance $d$ between centers:
   $$d = \sqrt{(x_R - x_M)^2 + (y_R - y_M)^2}$$
3. **Composite Scoring**: Evaluates a weighted combination of distance and overlap:
   $$\text{score} = 0.60 \times \text{overlap\_ratio} + 0.40 \times \left(1.0 - \frac{d}{d_{\text{max}}}\right)$$
4. **Ambiguity Resolution**: Assigns riders with overlapping candidates to the motorcycle yielding the highest composite score.
5. **Rider Ordering**: Sorts occupant riders relative to the motorcycle's flow direction using `TrajectoryService` heading vectors:
   - **Incoming ($dy > 0$)**: Motorcycle travels down. Front is at the bottom, so riders are sorted by y-coordinate descending.
   - **Outgoing ($dy < 0$)**: Motorcycle travels up. Front is at the top, so riders are sorted by y-coordinate ascending.

---

## 4. Configuration

Values are stored in [pipeline.yaml](file:///c:/Users/samee/Desktop/Traffic%20Violation/configs/pipeline.yaml):

```yaml
  rider_association:
    minimum_iou: 0.15
    maximum_distance: 150.0
    association_score_threshold: 0.40
    minimum_confidence: 0.50
    maximum_passengers: 3
```

---

## 5. Performance & Limitations

- **Performance**: Performs a single mapping pass per frame. Easily handles 100 motorcycles and 300 riders in **<15ms**, ensuring seamless execution.
- **Limitations**: In cases of extreme occlusion (e.g. rider blocks motorcycle box completely), the association score can drop below the threshold, resulting in unassigned riders.
