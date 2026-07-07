# Dataset Report - Traffic Violation AI

This document details the state of the datasets in `datasets/` after project reorganization.

## Dataset Summary

| Dataset Name | Task Category | Current Format | YOLO Ready? | File Integrity Issues |
| --- | --- | --- | --- | --- |
| **`computer_vision`** | Detection | YOLO TXT | ✅ Yes | Clean. Missing `test/` split folders created as placeholders. |
| **`driver_behavior`** | Classification | YOLO TXT | ✅ Yes | Clean. 156 duplicate images found. 17 empty labels. |
| **`helmet`** | Detection | YOLO TXT | ✅ Yes | Clean. |
| **`number_plate`** | Detection | Pascal VOC XML | ❌ No | Requires XML-to-TXT conversion. 47 duplicates. 1 missing image. |
| **`number_plate_ocr`** | OCR | Tabular TSV | ❌ No | Kept separate. Designed for character recognition, not detection. |
| **`seat_belt`** | Detection | YOLO TXT / Seg | ⚠️ Partial | Unnested. Contains polygon segmentation annotations. 138 empty labels, 250 duplicates. Mismatches: 74 missing labels, 303 missing images. Classes.txt has 4 classes, but labels use 5. |
| **`traffic_light`** | Detection | Custom JSON | ❌ No | Requires COCO JSON-to-YOLO conversion. Placeholder splits created. |
| **`vehicle`** | Detection | Empty | ❌ No | Empty folder. |

## Required Action Items

1. **`number_plate` conversion**: Convert `.xml` bounding box files to YOLO normalized `.txt` format. Map all unique license plate texts (984 unique classes) to a single class ID `0` (`license_plate`).
2. **`traffic_light` conversion**: Convert `train.json` to individual YOLO text annotation files. Convert absolute pixel coordinates (`xmin, ymin, xmax, ymax`) to normalized box coordinates.
3. **`seat_belt` class alignment**: Map class ID `4` (which exists in label files but is not listed in `classes.txt`) to the correct label, or update `classes.txt` to contain 5 entries.
4. **`seat_belt` segmentation format**: Decide whether to train a YOLO instance segmentation model or write a downsampling converter to turn polygons into 5-value bounding box lines.
5. **Deduplication**: Run a script to remove duplicate files to prevent validation set leakage.