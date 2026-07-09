# Seat Belt Detection Module

The **Seat Belt Detection Module** runs real-time seat belt checks for vehicle occupants (Driver and Front Passenger) within the STVDS pipeline.

---

## 1. Dataset Overview & Validation Report

The dataset is located in `datasets/detection/seat_belt/` and has been validated:

### Current Dataset Split File Counts

| Split | Images | Labels | Status |
| :--- | :--- | :--- | :--- |
| **Train** | 3708 | 3709 | Contains 1 helper `classes.txt` in the `labels/` directory (normal) |
| **Validation** | 657 | 685 | **⚠️ Split Mismatch** (28 label files are missing corresponding images) |
| **Test** | 579 | 551 | **⚠️ Split Mismatch** (28 image files are missing corresponding labels) |

### Mismatch Analysis
There are exactly 28 files (e.g. `frame8354`, `WIN_20221213_15_57_38_Pro_172`, `frame8352`) whose images reside in `test/images/` but their corresponding `.txt` labels reside in `valid/labels/`. This cross-split mismatch causes training tools to report missing labels or images for these 28 pairs.

### Class Mapping
The dataset contains 5 classes:
- Class `0`: `yawn`
- Class `1`: `eyesclosed`
- Class `2`: `seatbelt`
- Class `3`: `mobile`
- Class `4`: `cigarette`

---

## 2. Training Workflow

A reusable CLI training script is available at [train.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/training/seat_belt/train.py).

### Directories Structure
```
training/seat_belt/
├── configs/
├── weights/
├── runs/
├── results/
├── logs/
└── checkpoints/
```

### CLI Command Options
```bash
python training/seat_belt/train.py \
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

## 3. Inference & Spatial Association

The module runs within the Pipeline Manager under [seatbelt_detection.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/detection/seatbelt_detection.py).

### Windshield Subdivision Logic
For each tracked eligible vehicle (`car`, `truck`, `bus`):
1. **Define Windshield Region**: Resolves the top 50% region of the vehicle bounding box.
2. **Splitting the Region**: Divides the windshield box vertically into:
   - **Right Half (Driver Windshield)**: `[wx1 + w_w/2, wy1, wx2, wy2]`
   - **Left Half (Passenger Windshield)**: `[wx1, wy1, wx1 + w_w/2, wy2]`
   *(Assumes Right-Hand Drive configuration standard).*

### Occupant & Compliance States
Since the dataset lacks a native `no_seatbelt` class, compliance is evaluated using face/body indicators:
- **Seat Belt ✅**: If a `seatbelt` (class 2) box is detected with its center inside the region.
- **No Seat Belt ❌**: If occupant indicators (yawn, eyesclosed, mobile, cigarette) are detected in the region, but **no** `seatbelt` box is found.
- **Unknown ⚪**: If no indicators are detected, indicating no occupant is visible in that region.

---

## 4. Pipeline Integration

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
Seat Belt Detection  <-- Runs here
       ↓
Result Aggregation
       ↓
Visualization Overlays
       ↓
Output Result
```

---

## 5. Known Limitations
- **Right-Hand Drive Assumption**: Windshield subdivision assumes Right-Hand Drive. If deployed in Left-Hand Drive countries, the left/right region mapping must be inverted.
- **Occlusions**: If the steering wheel, dashboards, or heavy windshield glares block the occupant, states revert to `Unknown ⚪` instead of false positive alerts.

---

## 6. Future Improvements
1. ** Windshield Segmentation**: Use semantic segmentation to isolate the windshield area, making cropping completely independent of vehicle height.
2. **Occupant Face Tracking**: Chain a facial landmark model to track the driver's head directly, removing spatial bounding box reliance.
