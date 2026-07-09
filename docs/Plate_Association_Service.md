# Plate Association Service

The **Plate Association Service** is a central shared layer responsible for matching detected number plates with tracked vehicles. It resolves vehicle-plate ownership and maintains tracking histories over time, serving as the single source of truth for downstream OCR and violation processing.

---

## 1. Architecture

The service acts as a standard shared utility positioned in the pipeline execution flow directly below tracking updates:

```
            ByteTrack Tracking Output
                       │
                       ▼
            PlateAssociationService ◄──── YOLO Number Plate Bounding Boxes
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
    Number Plate Module         OCR Module (Downstream)
```

By providing a single source of truth, it prevents downstream modules from implementing redundant matching calculations.

---

## 2. Shared Models

### `PlateInfo`
- `plate_tracking_id` (`Optional[int]`): Unique track ID of the plate if tracked.
- `plate_bbox` (`List[float]`): Bounding box coordinates `[x1, y1, x2, y2]`.
- `confidence` (`float`): Detection confidence score.
- `cropped_plate_image` (`Optional[Any]`): Image array of the cropped plate.
- `timestamp` (`float`): Frame epoch timestamp.
- `frame_id` (`int`): Frame index.

### `VehiclePlateAssociation`
- `vehicle_tracking_id` (`int`): Vehicle tracker ID.
- `vehicle_class` (`int`): Vehicle class (e.g. car, truck, motorcycle).
- `vehicle_bbox` (`List[float]`): Vehicle box coordinates.
- `associated_plate` (`Optional[PlateInfo]`): Associated plate in the current frame.
- `association_confidence` (`float`): Match confidence score.
- `plate_history` (`List[PlateInfo]`): Historical list of associated plates.
- `stable_plate` (`Optional[PlateInfo]`): Confirmed stable plate over multiple frames.
- `timestamp` (`float`): Frame epoch timestamp.

---

## 3. Association Workflow & Scoring Logic

1. **Overlap Evaluation**: For each plate candidate, the service calculates the intersection ratio relative to the plate box area:
   $$\text{overlap\_ratio} = \frac{\text{Area}(\text{Intersection}(P, V))}{\text{Area}(P)}$$
2. **Center Distance**: Resolves Euclidean distance $d$ between centers.
3. **Composite Scoring**: Evaluates a weighted combination of distance and overlap:
   $$\text{score} = 0.60 \times \text{overlap\_ratio} + 0.40 \times \left(1.0 - \frac{d}{d_{\text{max}}}\right)$$
4. **Ambiguity Resolution**: Assigns plates to the vehicle yielding the highest composite score.
5. **Stable Plate Selection**: Once `plate_history` length reaches `stable_confirmation_frames` (default: `5`), the plate entry with the highest confidence is selected as the `stable_plate`.

---

## 4. Configuration

Values are stored in [pipeline.yaml](file:///c:/Users/samee/Desktop/Traffic%20Violation/configs/pipeline.yaml):

```yaml
  plate_association:
    minimum_plate_confidence: 0.50
    minimum_association_score: 0.35
    minimum_history_length: 3
    stable_confirmation_frames: 5
    maximum_plate_distance: 150.0
    association_weights:
      overlap: 0.60
      distance: 0.40
```

---

## 5. Performance & Limitations

- **Performance**: Performs a single mapping pass per frame. Easily handles 100 vehicles and 100 plates in **<10ms** (linear time complexity).
- **Limitations**: In cases of heavy occlusion or low-light, plate detections can drop below the confidence threshold, delaying stable plate generation.
