# Mobile Phone Detection Module

The **Mobile Phone Detection Module** targets driver distraction by detecting phone usage within the driver windshield zone of tracked vehicles.

---

## 1. Dataset Overview & Validator Report

The dataset utilized is located in `datasets/classification/driver_behavior/` (which contains YOLO bounding box annotations):

### Dataset Split File Counts
- **Train**: 3708 images / 3708 labels
- **Validation**: 657 images / 657 labels (aligned after excluding the 28 mismatched pairs)
- **Test**: 579 images / 579 labels

### Class Mapping
- Class `0`: `cigarette` (Occupant indicator)
- Class `1`: `phone` (Mobile Phone usage)
- Class `2`: `seatbelt` (Occupant indicator)

---

## 2. Training Workflow

A reusable CLI training script is available at [train.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/training/mobile_phone/train.py).

### Directory Structure
```
training/mobile_phone/
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
python training/mobile_phone/train.py \
  --epochs 50 \
  --batch 16 \
  --imgsz 640 \
  --patience 10 \
  --model-size n \
  --device 0 \
  --resume \
  --export onnx
```

---

## 3. Driver Region Service

A centralized utility service [driver_region_service.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/services/driver_region_service.py) computes region boxes for all interior vehicle modules.

### Windshield Division Method
```python
regions = DriverRegionService.get_occupant_regions(vehicle_xyxy, windshield_height_ratio=0.50, drive_side="RHD")
driver_box = regions["driver"]
passenger_box = regions["passenger"]
```

This prevents duplicate code math in `SeatBeltDetectionModule` and `MobilePhoneDetectionModule`.

---

## 4. Inference & BBox Spatial Matching

The mobile phone module runs under [mobile_phone_detection.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/detection/mobile_phone_detection.py):

### Detection Scope
- **Evaluation Filter**: Evaluates only the resolved `driver_box` region of eligible tracked vehicles (`car`, `truck`, `bus`). Ignores passengers, pedestrians, and motorcyclists.
- **States Resolution**:
  - **Mobile Phone 📱**: If a `phone` (class 1) bbox center falls inside the driver region.
  - **No Mobile Phone ✅**: If occupant indicators (cigarette, seatbelt, or other classes) are detected in the driver region, but **no** phone is detected.
  - **Unknown ⚪**: If no detections fall inside the region, implying the driver is not visible or obscured.

---

## 5. Pipeline Integration

Registered dynamically inside the Pipeline Manager:

```
Frame Validation
       ↓
Frame Preprocessing
       ↓
YOLO Detection (Vehicle classes)
       ↓
ByteTrack Tracking
       ↓
Helmet Detection
       ↓
Seat Belt Detection
       ↓
Mobile Phone Detection  <-- Runs here
       ↓
Result Aggregation
       ↓
Visualization Overlays
       ↓
Output Result
```

---

## 6. Known Limitations
- **LHD/RHD Dependency**: Subdivisions are set for Right-Hand Drive. Must be configured if LHD is used.
- **Low Confidence**: Reverts to `Unknown` rather than flagging false positives if visual resolution is low.

---

## 7. Future Improvements
1. **Face Orientation Integration**: Run gaze/face orientation to detect if the driver is looking down (distracted) even if the phone is not visible.
2. **Temporal Window Smoothing**: Accumulate states across multiple tracking frames to filter out classification flickers.
