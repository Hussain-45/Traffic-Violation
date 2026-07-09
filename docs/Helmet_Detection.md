# Helmet Detection Module

The **Helmet Detection Module** runs real-time helmet vs. no-helmet classification for motorcycle riders within the STVDS pipeline.

---

## 1. Dataset Verification & Statistics

The dataset is located in `datasets/detection/helmet/` and was validated with the following image, label, and annotation split distribution:

### Dataset Splits

| Split | Images | BBoxes / Annotations | Class 0 (Helmet) | Class 1 (No Helmet) |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | 699 | 1170 | 384 | 786 |
| **Valid** | 88 | 137 | 51 | 86 |
| **Test** | 88 | 152 | 54 | 98 |
| **Total** | 875 | 1459 | 489 | 970 |

- **YOLO format**: Class annotations use normalizations coordinates `[class_id, x_center, y_center, width, height]`.
- **Integrity**: Verified 1:1 image-to-label mappings with no missing or corrupted label files.

---

## 2. Training Pipeline

A reusable CLI training script is available at [train.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/training/helmet/train.py).

### Directories Structure
```
training/helmet/
├── configs/
├── weights/
├── runs/
├── results/
├── logs/
└── checkpoints/
```

### CLI Command Options
```bash
python training/helmet/train.py \
  --epochs 50 \
  --batch 16 \
  --imgsz 640 \
  --patience 10 \
  --model-size n \
  --device 0 \
  --resume \
  --export onnx
```

- **Early Stopping**: Controlled via `--patience` parameter.
- **Checkpoints & Resume**: Auto-saves checkpoints inside `checkpoints/last.pt` to recover training runs with `--resume`.
- **Export Formats**: Supports exporting the best weights directly to ONNX or TensorRT Engine formats.

---

## 3. Inference & Spatial Matching Logic

The module runs within the Pipeline Manager under [helmet_detection.py](file:///c:/Users/samee/Desktop/Traffic%20Violation/ai/detection/helmet_detection.py).

### Detection Scope
- **Evaluation Filter**: Helmet evaluation is only performed on tracked `motorcycle` objects and associated `person` riders. Bypasses cars, trucks, buses, and general pedestrians.
- **Overlapping Rider Resolution**:
  - Compares tracked `person` bounding boxes with tracked `motorcycle` bounding boxes.
  - If a person has > 10% overlap intersection with a motorcycle, they are labeled a rider.
  - If no explicit person track is overlapping, the top 50% of the motorcycle bounding box serves as a fallback.

### Spatial Containment Check
1. Runs the YOLOv8 helmet model on the full image frame (reducing inference overhead to one pass).
2. Maps helmet/no-helmet predictions to riders by verifying if the prediction center falls inside the head region (upper 45% of the rider's height box).
3. If multiple boxes intersect, picks the box with the highest overlap ratio.

---

## 4. Pipeline Integration

Registered dynamically inside the central AI Pipeline Manager:

```
Frame Validation
       ↓
Frame Preprocessing
       ↓
YOLO Detection
       ↓
ByteTrack Tracking
       ↓
Helmet Detection (Exposes counts & marks violators)
       ↓
Result Aggregation
       ↓
Visualization Overlays (Draws status badges)
       ↓
Output Result
```

- Configured using [models.yaml](file:///c:/Users/samee/Desktop/Traffic%20Violation/configs/models.yaml) to switch weights between different model sizes (`n`, `s`, `m`, `l`, `x`).
- Integrated inside the status API endpoints to stream count metrics and state statuses directly to the Next.js frontend.

---

## 5. Future Improvements

1. **Rider Pose Detection**: Implement Keypoint/Pose estimation to segment the rider's neck/head line explicitly, enhancing overlap resolution.
2. **Hard-Negative Mining**: Collect false-positive images (e.g. backpacks, round bags associated as helmets) and feed them back to the training dataset.
3. **Temporal Smoothing**: Use a rolling window track history to smooth out single-frame classification flickers (e.g. if a rider is detected without a helmet for 1 frame but with a helmet for 10 frames, smooth to Helmet).
