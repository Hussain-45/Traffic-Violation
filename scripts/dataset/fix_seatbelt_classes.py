"""
Seat Belt Dataset Class Alignment & Cleanup
============================================
Fixes all inconsistencies in the seat_belt dataset:
1. Updates classes.txt to include all 5 classes (adds 'cigarette')
2. Converts string class names to numeric IDs
3. Converts polygon segmentation lines to bounding box format
4. Removes orphan label files (no matching image)
5. Creates a validation split from training data (15%)
6. Reports full class distribution statistics

Source: datasets/detection/seat_belt/
"""

import os
import sys
import re
import shutil
import random
from pathlib import Path
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "datasets" / "detection" / "seat_belt"
VALID_SPLIT_RATIO = 0.15  # Take 15% of train for validation
RANDOM_SEED = 42

# Definitive class mapping — class 4 (cigarette) was missing from classes.txt
CLASS_MAP = {
    "yawn":      0,
    "eyesclosed": 1,
    "seatbelt":  2,
    "mobile":    3,
    "cigarette": 4,
    # Numeric strings
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
}
CLASS_NAMES = ["yawn", "eyesclosed", "seatbelt", "mobile", "cigarette"]

# Image extensions we recognize
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def get_image_stems(directory: Path) -> set[str]:
    """Get set of file stems for all images in a directory."""
    if not directory.exists():
        return set()
    return {f.stem for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS}


def get_label_stems(directory: Path) -> set[str]:
    """Get set of file stems for all .txt label files."""
    if not directory.exists():
        return set()
    return {f.stem for f in directory.iterdir()
            if f.is_file() and f.suffix == ".txt" and f.stem != "classes"}


def polygon_to_bbox(coords: list[float]) -> tuple[float, float, float, float]:
    """
    Convert polygon coordinates to bounding box.
    Polygon format: x1 y1 x2 y2 x3 y3 ...
    Returns: (x_center, y_center, width, height) — all normalized [0,1]
    """
    xs = [coords[i] for i in range(0, len(coords), 2)]
    ys = [coords[i] for i in range(1, len(coords), 2)]

    x_min = min(xs)
    x_max = max(xs)
    y_min = min(ys)
    y_max = max(ys)

    x_center = (x_min + x_max) / 2.0
    y_center = (y_min + y_max) / 2.0
    width    = x_max - x_min
    height   = y_max - y_min

    return (x_center, y_center, width, height)


def fix_label_file(label_path: Path, stats: dict) -> list[str]:
    """
    Fix a single label file. Returns list of corrected YOLO lines.

    Handles:
    - String class names → numeric IDs
    - Unknown class IDs → skip with warning
    - Polygon lines (>5 values) → bounding box conversion
    - Empty lines → skip
    - Malformed lines → skip with warning
    """
    fixed_lines = []

    with open(label_path, "r", encoding="utf-8", errors="replace") as f:
        raw_lines = f.readlines()

    for line_num, raw_line in enumerate(raw_lines, 1):
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 2:
            stats["malformed_lines"] += 1
            continue

        # ── Resolve class ID ──
        class_token = parts[0]

        if class_token in CLASS_MAP:
            class_id = CLASS_MAP[class_token]
        else:
            # Try to parse as integer
            try:
                class_id = int(class_token)
                if class_id < 0 or class_id >= len(CLASS_NAMES):
                    stats["unknown_class_ids"] += 1
                    continue
            except ValueError:
                stats["unknown_class_names"] += 1
                continue

        # ── Handle string class name conversion ──
        if not class_token.isdigit():
            stats["string_to_numeric"] += 1

        # ── Parse coordinates ──
        try:
            coords = [float(v) for v in parts[1:]]
        except ValueError:
            stats["malformed_lines"] += 1
            continue

        # ── Determine if bounding box or polygon ──
        if len(coords) == 4:
            # Standard YOLO bbox: x_center y_center width height
            x_center, y_center, width, height = coords
            stats["bbox_lines"] += 1

        elif len(coords) >= 6 and len(coords) % 2 == 0:
            # Polygon segmentation: convert to bbox
            x_center, y_center, width, height = polygon_to_bbox(coords)
            stats["polygon_to_bbox"] += 1

        else:
            stats["malformed_lines"] += 1
            continue

        # ── Validate and clamp values ──
        x_center = max(0.0, min(1.0, x_center))
        y_center = max(0.0, min(1.0, y_center))
        width    = max(0.001, min(1.0, width))
        height   = max(0.001, min(1.0, height))

        # Ensure the box stays within [0, 1] after centering
        if x_center - width / 2 < 0:
            width = x_center * 2
        if x_center + width / 2 > 1:
            width = (1 - x_center) * 2
        if y_center - height / 2 < 0:
            height = y_center * 2
        if y_center + height / 2 > 1:
            height = (1 - y_center) * 2

        stats["class_distribution"][class_id] += 1
        fixed_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    return fixed_lines


def process_split(split_name: str, images_dir: Path, labels_dir: Path, stats: dict):
    """Process all labels in a split directory."""
    print(f"\n  ── Processing {split_name} ──")

    if not labels_dir.exists():
        print(f"    Labels dir does not exist: {labels_dir}")
        return

    image_stems = get_image_stems(images_dir)
    label_stems = get_label_stems(labels_dir)

    print(f"    Images: {len(image_stems)}")
    print(f"    Labels: {len(label_stems)}")

    # Find orphans
    orphan_labels = label_stems - image_stems
    orphan_images = image_stems - label_stems

    if orphan_labels:
        print(f"    Orphan labels (no image): {len(orphan_labels)}")
        stats["orphan_labels_removed"] += len(orphan_labels)

        # Remove orphan labels
        for stem in orphan_labels:
            orphan_path = labels_dir / f"{stem}.txt"
            if orphan_path.exists():
                orphan_path.unlink()

    if orphan_images:
        print(f"    Orphan images (no label): {len(orphan_images)} — creating empty labels")
        # Create empty label files for orphan images (negative examples)
        for stem in orphan_images:
            empty_lbl = labels_dir / f"{stem}.txt"
            if not empty_lbl.exists():
                empty_lbl.write_text("")
                stats["empty_labels_created"] += 1

    # Fix all remaining label files
    # Re-read after orphan removal
    label_files = sorted(labels_dir.glob("*.txt"))
    fixed_count = 0

    for lbl_path in label_files:
        if lbl_path.stem == "classes":
            continue

        fixed_lines = fix_label_file(lbl_path, stats)

        # Write fixed content back
        with open(lbl_path, "w", encoding="utf-8") as f:
            if fixed_lines:
                f.write("\n".join(fixed_lines) + "\n")

        fixed_count += 1

    print(f"    Labels fixed: {fixed_count}")


def create_validation_split(dataset_dir: Path, ratio: float = 0.15):
    """
    Create a validation split from the training set.
    Moves a portion of train images+labels to valid/.
    """
    train_img_dir = dataset_dir / "train" / "images"
    train_lbl_dir = dataset_dir / "train" / "labels"
    valid_img_dir = dataset_dir / "valid" / "images"
    valid_lbl_dir = dataset_dir / "valid" / "labels"

    if not train_img_dir.exists():
        print("  [WARN] No train/images/ directory found, skipping validation split")
        return 0

    # Check if valid already has data
    existing_valid = get_image_stems(valid_img_dir)
    if existing_valid:
        print(f"  Validation set already has {len(existing_valid)} images, skipping split")
        return 0

    valid_img_dir.mkdir(parents=True, exist_ok=True)
    valid_lbl_dir.mkdir(parents=True, exist_ok=True)

    # Get paired stems (both image and label exist)
    image_stems = get_image_stems(train_img_dir)
    label_stems = get_label_stems(train_lbl_dir)
    paired_stems = sorted(image_stems & label_stems)

    n_valid = int(len(paired_stems) * ratio)
    if n_valid == 0:
        return 0

    random.seed(RANDOM_SEED)
    valid_stems = set(random.sample(paired_stems, n_valid))

    moved = 0
    for stem in valid_stems:
        # Find and move image
        for ext in IMAGE_EXTS:
            img_src = train_img_dir / f"{stem}{ext}"
            if img_src.exists():
                shutil.move(str(img_src), str(valid_img_dir / img_src.name))
                break

        # Move label
        lbl_src = train_lbl_dir / f"{stem}.txt"
        if lbl_src.exists():
            shutil.move(str(lbl_src), str(valid_lbl_dir / lbl_src.name))

        moved += 1

    print(f"  Created validation split: {moved} samples moved from train → valid")
    return moved


def update_classes_txt(dataset_dir: Path):
    """Write the corrected classes.txt with all 5 classes."""
    classes_path = dataset_dir / "classes.txt"

    print(f"\n  ── Updating classes.txt ──")
    print(f"    Old content:")
    if classes_path.exists():
        old_content = classes_path.read_text().strip()
        for line in old_content.split("\n"):
            print(f"      {line.strip()}")
    else:
        print(f"      (file does not exist)")

    new_content = "\n".join(CLASS_NAMES) + "\n"
    with open(classes_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"    New content:")
    for i, name in enumerate(CLASS_NAMES):
        print(f"      {i}: {name}")


def create_data_yaml(dataset_dir: Path):
    """Generate data.yaml for YOLOv8 training."""
    yaml_content = f"""# Seat Belt / Driver Distraction Detection — YOLOv8 Dataset Config
# Auto-generated by fix_seatbelt_classes.py

path: {dataset_dir.as_posix()}
train: train/images
val: valid/images
test: test/images

nc: {len(CLASS_NAMES)}
names: {CLASS_NAMES}
"""
    yaml_path = dataset_dir / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"  Written: {yaml_path}")


def validate_output(dataset_dir: Path):
    """Run validation checks on all splits."""
    print("\n══════════════════════════════════════════")
    print("  VALIDATION CHECKS")
    print("══════════════════════════════════════════")

    errors = 0
    for split in ["train", "valid", "test"]:
        lbl_dir = dataset_dir / split / "labels"
        img_dir = dataset_dir / split / "images"

        if not lbl_dir.exists():
            continue

        label_files = [f for f in lbl_dir.iterdir() if f.suffix == ".txt" and f.stem != "classes"]

        bad_format = 0
        string_classes = 0
        out_of_range = 0

        for lbl_path in label_files[:50]:  # Spot-check 50 files
            with open(lbl_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()

                    if len(parts) != 5:
                        bad_format += 1
                        continue

                    # Check class is numeric
                    if not parts[0].isdigit():
                        string_classes += 1
                        continue

                    try:
                        cls_id = int(parts[0])
                        vals = [float(v) for v in parts[1:]]

                        if cls_id < 0 or cls_id >= len(CLASS_NAMES):
                            out_of_range += 1

                        for v in vals:
                            if v < 0.0 or v > 1.0:
                                out_of_range += 1
                    except ValueError:
                        bad_format += 1

        status = "PASS" if (bad_format == 0 and string_classes == 0 and out_of_range == 0) else "WARN"
        if bad_format > 0 or string_classes > 0 or out_of_range > 0:
            errors += 1

        img_count = len(get_image_stems(img_dir))
        lbl_count = len(label_files)
        print(f"  [{status}] {split}: {img_count} images, {lbl_count} labels"
              f" | bad_format={bad_format}, string_classes={string_classes}, out_of_range={out_of_range}")

    if errors == 0:
        print("\n  ✅ All validation checks PASSED")
    else:
        print(f"\n  ⚠️  {errors} validation issues found")


def main():
    print("╔══════════════════════════════════════════╗")
    print("║  Seat Belt Dataset Class Alignment       ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Dataset: {DATASET_DIR}")

    if not DATASET_DIR.exists():
        print(f"  [FATAL] Dataset directory does not exist: {DATASET_DIR}")
        sys.exit(1)

    # Stats tracker
    stats = {
        "string_to_numeric": 0,
        "polygon_to_bbox": 0,
        "bbox_lines": 0,
        "malformed_lines": 0,
        "unknown_class_ids": 0,
        "unknown_class_names": 0,
        "orphan_labels_removed": 0,
        "empty_labels_created": 0,
        "class_distribution": defaultdict(int),
    }

    # Step 1: Update classes.txt
    update_classes_txt(DATASET_DIR)

    # Step 2: Fix labels in each split
    print("\n── Step 2: Fixing Label Files ──")
    for split in ["train", "test"]:
        img_dir = DATASET_DIR / split / "images"
        lbl_dir = DATASET_DIR / split / "labels"
        process_split(split, img_dir, lbl_dir, stats)

    # Step 3: Create validation split
    print("\n── Step 3: Creating Validation Split ──")
    create_validation_split(DATASET_DIR, VALID_SPLIT_RATIO)

    # Also fix the new validation labels (they were already fixed in train)
    valid_lbl_dir = DATASET_DIR / "valid" / "labels"
    if valid_lbl_dir.exists() and any(valid_lbl_dir.iterdir()):
        valid_img_dir = DATASET_DIR / "valid" / "images"
        # These labels were already fixed before being moved, so just log counts
        v_imgs = len(get_image_stems(valid_img_dir))
        v_lbls = len(get_label_stems(valid_lbl_dir))
        print(f"  Validation split: {v_imgs} images, {v_lbls} labels")

    # Step 4: Generate data.yaml
    print("\n── Step 4: Generating data.yaml ──")
    create_data_yaml(DATASET_DIR)

    # Step 5: Print summary
    print("\n══════════════════════════════════════════")
    print("  PROCESSING SUMMARY")
    print("══════════════════════════════════════════")
    print(f"  String→Numeric conversions: {stats['string_to_numeric']}")
    print(f"  Polygon→BBox conversions:   {stats['polygon_to_bbox']}")
    print(f"  Standard bbox lines:        {stats['bbox_lines']}")
    print(f"  Malformed lines removed:    {stats['malformed_lines']}")
    print(f"  Unknown class IDs skipped:  {stats['unknown_class_ids']}")
    print(f"  Unknown class names skipped: {stats['unknown_class_names']}")
    print(f"  Orphan labels removed:      {stats['orphan_labels_removed']}")
    print(f"  Empty labels created:       {stats['empty_labels_created']}")
    print(f"\n  Class Distribution:")
    for cls_id in sorted(stats["class_distribution"].keys()):
        cls_name = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else f"unknown_{cls_id}"
        count = stats["class_distribution"][cls_id]
        print(f"    {cls_id}: {cls_name:15s} → {count:,} annotations")

    # Step 6: Validate
    validate_output(DATASET_DIR)

    print("\n══════════════════════════════════════════")
    print("  CLASS ALIGNMENT COMPLETE ✓")
    print("══════════════════════════════════════════")


if __name__ == "__main__":
    main()
