"""
JSON to YOLO Converter — Traffic Light Dataset
================================================
Converts custom traffic light JSON annotations to YOLO TXT format.
Uses PIL to read actual image dimensions for accurate coordinate normalization.

Source: datasets/detection/traffic_light/train_dataset/train.json + train_images/
Output: datasets/detection/traffic_light_yolo/ with train/valid/test splits

Class mapping:
  0: red
  1: green
  2: yellow
  3: unknown (color not specified)
  4: traffic_light (outer housing box)
"""

import os
import sys
import json
import shutil
import random
from pathlib import Path
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "datasets" / "detection" / "traffic_light"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "detection" / "traffic_light_yolo"
TRAIN_RATIO = 0.80
VALID_RATIO = 0.10
TEST_RATIO  = 0.10
RANDOM_SEED = 42

CLASS_MAP = {
    "red": 0,
    "green": 1,
    "yellow": 2,
    "unknown": 3,
}
HOUSING_CLASS_ID = 4  # The outer traffic light housing box
CLASS_NAMES = ["red", "green", "yellow", "unknown", "traffic_light"]


def get_image_dimensions(image_path: Path) -> tuple[int, int] | None:
    """
    Get image width and height. Uses PIL if available, falls back to
    reading JPEG/PNG headers manually for speed.
    """
    try:
        from PIL import Image
        with Image.open(str(image_path)) as img:
            return img.size  # (width, height)
    except ImportError:
        pass

    # Fallback: try to read JPEG header
    try:
        with open(image_path, "rb") as f:
            data = f.read(65536)

        # JPEG
        if data[:2] == b'\xff\xd8':
            i = 2
            while i < len(data) - 1:
                if data[i] != 0xFF:
                    break
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    height = int.from_bytes(data[i+5:i+7], 'big')
                    width  = int.from_bytes(data[i+7:i+9], 'big')
                    return (width, height)
                else:
                    length = int.from_bytes(data[i+2:i+4], 'big')
                    i += 2 + length

        # PNG
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            width  = int.from_bytes(data[16:20], 'big')
            height = int.from_bytes(data[20:24], 'big')
            return (width, height)

    except Exception:
        pass

    return None


def convert_bbox_to_yolo(xmin: float, ymin: float, xmax: float, ymax: float,
                         img_w: int, img_h: int) -> tuple[float, float, float, float] | None:
    """
    Convert absolute pixel coordinates to YOLO normalized format.
    Returns (x_center, y_center, width, height) all in [0, 1], or None if invalid.
    """
    # Clamp to image boundaries
    xmin = max(0.0, min(float(xmin), img_w))
    ymin = max(0.0, min(float(ymin), img_h))
    xmax = max(0.0, min(float(xmax), img_w))
    ymax = max(0.0, min(float(ymax), img_h))

    # Validate positive area
    if xmax <= xmin or ymax <= ymin:
        return None

    x_center = ((xmin + xmax) / 2.0) / img_w
    y_center = ((ymin + ymax) / 2.0) / img_h
    box_w    = (xmax - xmin) / img_w
    box_h    = (ymax - ymin) / img_h

    # Final range check
    if not (0.0 <= x_center <= 1.0 and 0.0 <= y_center <= 1.0 and
            0.0 < box_w <= 1.0 and 0.0 < box_h <= 1.0):
        return None

    return (x_center, y_center, box_w, box_h)


def parse_train_json(json_path: Path) -> dict:
    """
    Parse the traffic light train.json file.
    Returns a dict mapping image filenames to their annotations.
    """
    print(f"  Loading JSON: {json_path} ({json_path.stat().st_size / 1024 / 1024:.1f} MB)")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    annotations = data.get("annotations", [])
    print(f"  Total annotation entries: {len(annotations)}")

    # Group by image filename
    image_annotations = defaultdict(list)
    ignored_count = 0
    valid_count = 0

    for ann in annotations:
        filename = ann.get("filename", "")
        # Normalize path separators and extract just the image name
        filename = filename.replace("\\", "/")
        image_name = filename.split("/")[-1] if "/" in filename else filename

        # Skip ignored annotations
        if ann.get("ignore", 0) == 1:
            ignored_count += 1
            continue

        valid_count += 1
        image_annotations[image_name].append(ann)

    print(f"  Valid annotations: {valid_count}")
    print(f"  Ignored annotations: {ignored_count}")
    print(f"  Unique images: {len(image_annotations)}")

    return dict(image_annotations)


def process_annotations(image_annotations: dict, train_images_dir: Path) -> list[dict]:
    """
    Process all annotations: resolve image dimensions and convert bounding boxes.
    Returns a list of processed entries.
    """
    results = []
    dim_cache = {}
    no_image_count = 0
    no_dim_count = 0
    class_counts = defaultdict(int)

    for image_name, anns in sorted(image_annotations.items()):
        image_path = train_images_dir / image_name
        if not image_path.exists():
            no_image_count += 1
            continue

        # Get image dimensions (cached)
        if image_name not in dim_cache:
            dims = get_image_dimensions(image_path)
            if dims is None:
                no_dim_count += 1
                continue
            dim_cache[image_name] = dims

        img_w, img_h = dim_cache[image_name]
        if img_w <= 0 or img_h <= 0:
            continue

        yolo_lines = []

        for ann in anns:
            bndbox = ann.get("bndbox", {})
            xmin = bndbox.get("xmin", 0)
            ymin = bndbox.get("ymin", 0)
            xmax = bndbox.get("xmax", 0)
            ymax = bndbox.get("ymax", 0)

            # Convert outer housing box
            yolo_box = convert_bbox_to_yolo(xmin, ymin, xmax, ymax, img_w, img_h)
            if yolo_box:
                yolo_lines.append((HOUSING_CLASS_ID, *yolo_box))
                class_counts["traffic_light"] += 1

            # Convert inner color boxes (inbox)
            for inbox in ann.get("inbox", []):
                color = inbox.get("color", "unknown").lower()
                class_id = CLASS_MAP.get(color, CLASS_MAP["unknown"])

                inner_box = inbox.get("bndbox", {})
                inner_yolo = convert_bbox_to_yolo(
                    inner_box.get("xmin", 0), inner_box.get("ymin", 0),
                    inner_box.get("xmax", 0), inner_box.get("ymax", 0),
                    img_w, img_h
                )
                if inner_yolo:
                    yolo_lines.append((class_id, *inner_yolo))
                    class_counts[color] += 1

        if yolo_lines:
            results.append({
                "image_name": image_name,
                "image_path": image_path,
                "yolo_lines": yolo_lines
            })

    print(f"\n  ── Processing Summary ──")
    print(f"  Images processed:  {len(results)}")
    print(f"  Missing images:    {no_image_count}")
    print(f"  Unreadable images: {no_dim_count}")
    print(f"  Class distribution:")
    for cls_name, count in sorted(class_counts.items()):
        cls_id = CLASS_MAP.get(cls_name, HOUSING_CLASS_ID)
        print(f"    {cls_id}: {cls_name:15s} → {count:,} boxes")

    return results


def split_dataset(entries: list[dict]) -> dict:
    """Split entries into train/valid/test sets."""
    random.seed(RANDOM_SEED)
    shuffled = entries.copy()
    random.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * TRAIN_RATIO)
    n_valid = int(n * VALID_RATIO)

    splits = {
        "train": shuffled[:n_train],
        "valid": shuffled[n_train:n_train + n_valid],
        "test":  shuffled[n_train + n_valid:]
    }

    print(f"  Split: train={len(splits['train'])}, valid={len(splits['valid'])}, test={len(splits['test'])}")
    return splits


def write_yolo_output(splits: dict, output_dir: Path):
    """Write YOLO-formatted labels and copy images."""
    total_labels = 0
    total_boxes = 0

    for split_name, entries in splits.items():
        img_dir = output_dir / split_name / "images"
        lbl_dir = output_dir / split_name / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for entry in entries:
            image_path = entry["image_path"]
            image_name = entry["image_name"]
            stem = Path(image_name).stem

            # Copy image
            img_dest = img_dir / image_name
            if not img_dest.exists():
                shutil.copy2(str(image_path), str(img_dest))

            # Write label
            lbl_dest = lbl_dir / (stem + ".txt")
            lines = []
            for class_id, xc, yc, w, h in entry["yolo_lines"]:
                lines.append(f"{class_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
                total_boxes += 1

            with open(lbl_dest, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            total_labels += 1

    print(f"  Total label files written: {total_labels}")
    print(f"  Total bounding boxes:      {total_boxes}")


def write_data_yaml(output_dir: Path):
    """Generate data.yaml for YOLOv8 training."""
    yaml_content = f"""# Traffic Light Detection — YOLOv8 Dataset Config
# Auto-generated by coco_to_yolo.py

path: {output_dir.as_posix()}
train: train/images
val: valid/images
test: test/images

nc: {len(CLASS_NAMES)}
names: {CLASS_NAMES}
"""
    yaml_path = output_dir / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"  Written: {yaml_path}")


def validate_output(output_dir: Path):
    """Run validation checks on the output."""
    print("\n══════════════════════════════════════════")
    print("  VALIDATION CHECKS")
    print("══════════════════════════════════════════")

    errors = 0
    for split in ["train", "valid", "test"]:
        img_dir = output_dir / split / "images"
        lbl_dir = output_dir / split / "labels"

        if not img_dir.exists():
            print(f"  [FAIL] {split}/images/ does not exist")
            errors += 1
            continue

        images = {f.stem for f in img_dir.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png"}}
        labels = {f.stem for f in lbl_dir.iterdir() if f.suffix == ".txt"}

        orphan_labels = labels - images
        missing_labels = images - labels

        if orphan_labels:
            print(f"  [WARN] {split}: {len(orphan_labels)} orphan labels")
            errors += 1
        if missing_labels:
            print(f"  [WARN] {split}: {len(missing_labels)} images without labels")
            errors += 1

        # Spot-check YOLO format
        sample_labels = list(lbl_dir.glob("*.txt"))[:10]
        for lbl_path in sample_labels:
            with open(lbl_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) != 5:
                        print(f"  [FAIL] {lbl_path.name}:{line_num} — expected 5 values, got {len(parts)}")
                        errors += 1
                        continue
                    try:
                        cls_id = int(parts[0])
                        vals = [float(v) for v in parts[1:]]
                        if cls_id < 0 or cls_id >= len(CLASS_NAMES):
                            print(f"  [FAIL] {lbl_path.name}:{line_num} — invalid class_id {cls_id}")
                            errors += 1
                        for v in vals:
                            if not (0.0 <= v <= 1.0):
                                print(f"  [FAIL] {lbl_path.name}:{line_num} — value {v} out of range")
                                errors += 1
                    except ValueError:
                        print(f"  [FAIL] {lbl_path.name}:{line_num} — non-numeric values")
                        errors += 1

        print(f"  [{'PASS' if errors == 0 else 'WARN'}] {split}: {len(images)} images, {len(labels)} labels")

    if errors == 0:
        print("\n  ✅ All validation checks PASSED")
    else:
        print(f"\n  ⚠️  {errors} validation issues found")


def main():
    print("╔══════════════════════════════════════════╗")
    print("║  JSON → YOLO Converter (Traffic Light)   ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Source: {SOURCE_DIR}")
    print(f"  Output: {OUTPUT_DIR}")

    train_json = SOURCE_DIR / "train_dataset" / "train.json"
    train_images_dir = SOURCE_DIR / "train_dataset" / "train_images"

    if not train_json.exists():
        print(f"  [FATAL] train.json not found: {train_json}")
        sys.exit(1)
    if not train_images_dir.exists():
        print(f"  [FATAL] train_images/ not found: {train_images_dir}")
        sys.exit(1)

    # Clean output
    if OUTPUT_DIR.exists():
        print(f"  Cleaning existing output directory...")
        shutil.rmtree(OUTPUT_DIR)

    # Step 1: Parse JSON
    print("\n── Step 1: Parsing train.json ──")
    image_annotations = parse_train_json(train_json)

    # Step 2: Process annotations
    print("\n── Step 2: Processing Annotations ──")
    entries = process_annotations(image_annotations, train_images_dir)

    if not entries:
        print("  [FATAL] No valid entries processed!")
        sys.exit(1)

    # Step 3: Split
    print("\n── Step 3: Splitting Dataset ──")
    splits = split_dataset(entries)

    # Step 4: Write output
    print("\n── Step 4: Writing YOLO Output ──")
    write_yolo_output(splits, OUTPUT_DIR)

    # Step 5: Generate data.yaml
    print("\n── Step 5: Generating data.yaml ──")
    write_data_yaml(OUTPUT_DIR)

    # Step 6: Validate
    validate_output(OUTPUT_DIR)

    print("\n══════════════════════════════════════════")
    print("  CONVERSION COMPLETE ✓")
    print("══════════════════════════════════════════")


if __name__ == "__main__":
    main()
