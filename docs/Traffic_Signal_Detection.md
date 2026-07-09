# Traffic Signal Detection Module

The **Traffic Signal Detection Module** tracks and classifies the state of traffic lights (🔴 Red, 🟡 Yellow, 🟢 Green, ⚪ Unknown) within a defined road scene region of interest (ROI).

---

## 1. Dataset Overview & Validator Report

The dataset is located at [datasets/detection/traffic_light_yolo/](file:///c:/Users/samee/Desktop/Traffic%20Violation/datasets/detection/traffic_light_yolo/):

### Dataset Split File Counts
- **Train**: 1887 images / 1887 labels
- **Validation**: 235 images / 235 labels
- **Test**: 237 images / 237 labels

### Class Mapping in data.yaml
- Class `0`: `red` (🔴 Red)
- Class `1`: `green` (🟢 Green)
- Class `2`: `yellow` (🟡 Yellow)
- Class `3`: `unknown` (⚪ Unknown)
- Class `4`: `traffic_light` (Raw traffic light outline box)

---

## 2. Training Workflow

A reusable training CLI script is available at [train.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/training/traffic_light/train.py).

### Directory Structure
```
training/traffic_light/
├── configs/
├── weights/
├── runs/
├── logs/
├── results/
├── exports/
└── checkpoints/
```

### CLI Command Options
```bash
python training/traffic_light/train.py \
  --epochs 50 \
  --batch 16 \
  --imgsz 640 \
  --patience 10 \
  --model-size n \
  --device cpu \
  --resume \
  --export onnx
```

---

## 3. Road Scene Service

Centralized in [road_scene_service.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/services/road_scene_service.py).

### ROIs Calculations
Exposes methods for scaling road geometries dynamically to frame dimensions:
- `get_traffic_light_roi(w, h)`: Restricts traffic signal lookups to the top 45% of the viewport.
- `get_intersection_roi(w, h)`: Target crossing region (middle/lower 60%).
- `get_stop_line_roi(w, h)`: Stop line bounding box (placeholder).
- `get_lane_region(w, h)`: Lane boundary region (placeholder).
- `is_in_roi(box, roi)`: Spatial inclusion filter.

---

## 4. Standardized Output Schema

Detections are packaged inside the Pydantic-based `DetectionResult` class from [detection_result.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/shared/schemas/detection_result.py):

```json
{
  "module_name": "traffic_signal_detection",
  "tracking_id": -1,
  "vehicle_class": -1,
  "region": [120.0, 50.0, 150.0, 120.0],
  "status": "Red",
  "confidence": 0.98,
  "timestamp": 1783584850.25,
  "frame_id": 1084,
  "metadata": {
    "signal_id": 1
  }
}
```

---

## 5. Pipeline Integration

Runs directly after Mobile Phone Detection:

```
Vehicle Tracking
       ↓
Helmet Detection
       ↓
Seat Belt Detection
       ↓
Mobile Phone Detection
       ↓
Traffic Signal Detection  <-- Runs here
       ↓
Result Aggregation
       ↓
Visualization
```

---

## 6. Known Limitations
- **Occlusions**: Trees, larger vehicles (trucks, buses) blocking the traffic light will result in an `Unknown` state.
- **Lighting/Contrast**: High solar glare or night shadows might drop confidence below thresholds.

---

## 7. Future Improvements
1. **Red Light Violation Integration**: Correlate red signal state with vehicle tracking boxes crossing the stop-line ROI to trigger violation events (Step 13).
2. **Temporal Signal Smoothing**: Smooth color classifications across subsequent frames to avoid flickering states.
