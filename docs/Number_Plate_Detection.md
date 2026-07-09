# Number Plate Detection Module (ANPR Stage 1)

The **Number Plate Detection** module runs YOLOv8 license plate detection on incoming video stream frames, crops detected plates, and maps ownership to tracked vehicles using `PlateAssociationService`.

---

## 1. Architecture

The overall pipeline execution flow follows the sequence below:

```
            ┌───────────────────────┐
            │   Vehicle Detection   │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   Vehicle Tracking    │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │Number Plate Detection │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │PlateAssociationService│
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │      OCR Module       │
            └───────────────────────┘
```

---

## 2. Shared Services Integration

- **PlateAssociationService**: Matched plates are cached here with track IDs, bounding boxes, association confidence score, crops, timestamp, and frame index.
- **Stable Plate Logic**: Detections are accumulated over `stable_confirmation_frames` (default: `5`). Once confirmed, the plate becomes "stable" and is flagged as ready for downstream OCR.

---

## 3. Standard DetectionResult Schema

```json
{
  "module_name": "number_plate_detection",
  "tracking_id": 10,
  "vehicle_class": 2,
  "status": "Stable Plate",
  "confidence": 0.85,
  "timestamp": 100.0,
  "frame_id": 42,
  "region": [100.0, 100.0, 300.0, 300.0],
  "metadata": {
    "plate_bbox": [150.0, 250.0, 250.0, 290.0],
    "association_confidence": 0.85,
    "plate_visibility": 1.0,
    "plate_crop_ready": true,
    "stable_plate": { ... }
  }
}
```

---

## 4. Configuration

Values are stored in [pipeline.yaml](file:///c:/Users/samee/Desktop/Traffic%20Violation/configs/pipeline.yaml):

```yaml
  number_plate_detection:
    enabled: true
    confidence_threshold: 0.50
    minimum_plate_confidence: 0.50
    minimum_crop_width: 30
    minimum_crop_height: 10
    minimum_visibility: 0.10
    association_score: 0.35
    stable_confirmation_frames: 5
```

---

## 5. Overlay Visualizations

- **Stable Plate**: Green box `(129, 185, 16)` and label `Vehicle #ID: ANPR STABLE`.
- **Detecting**: Yellow box `(16, 185, 245)` and label `Vehicle #ID: ANPR DETECTING`.
- **Unknown**: Gray box `(150, 150, 150)` and label `Vehicle #ID: ANPR UNKNOWN`.
- Draws plate bounding boxes and association lines linking plates to vehicle center points.
