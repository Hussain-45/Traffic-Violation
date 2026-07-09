"""
XML to YOLO Converter — Number Plate Dataset
=============================================
Converts Pascal VOC XML annotations to YOLO TXT format.
All license plate text labels are mapped to a single class ID 0 (license_plate).

Source: datasets/detection/number_plate/ (google_images, video_images, State-wise_OLX)
Output: datasets/detection/number_plate_yolo/ with train/valid/test splits (80/10/10)
"""

import os
import sys
import xml.etree.ElementTree as ET
import shutil
import random
import hashlib
from pathlib import Path
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "datasets" / "detection" / "number_plate"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "detection" / "number_plate_yolo"
TRAIN_RATIO = 0.80
VALID_RATIO = 0.10
TEST_RATIO  = 0.10
RANDOM_SEED = 42
CLASS_NAMES = ["license_plate"]


def parse_voc_xml(xml_path: Path) -> dict | None:
    """
    Parse a Pascal VOC XML annotation file.
    Returns dict with filename, image size, and list of bounding boxes,
    or None if the file cannot be parsed.
    """
    try:
        tree = ET.parse(str(xml_path))
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"  [ERROR] XML parse error in {xml_path.name}: {e}")
        return None

    # Extract image filename
    filename_elem = root.find("filename")
    if filename_elem is None or not filename_elem.text:
        print(f"  [WARN] No <filename> in {xml_path.name}, skipping")
        return None

    # Extract image dimensions
    size_elem = root.find("size")
    if size_elem is None:
        print(f"  [WARN] No <size> in {xml_path.name}, skipping")
        return None

    try:
        width  = int(size_elem.findtext("width", "0"))
        height = int(size_elem.findtext("height", "0"))
    except ValueError:
        print(f"  [WARN] Invalid size values in {xml_path.name}, skipping")
        return None

    if width <= 0 or height <= 0:
        print(f"  [WARN] Zero/negative dimensions in {xml_path.name} (w={width}, h={height}), skipping")
        return None

    # Extract all bounding boxes
    boxes = []
    for obj in root.findall("object"):
        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue

        try:
            xmin = float(bndbox.findtext("xmin", "0"))
            ymin = float(bndbox.findtext("ymin", "0"))
            xmax = float(bndbox.findtext("xmax", "0"))
            ymax = float(bndbox.findtext("ymax", "0"))
        except ValueError:
            print(f"  [WARN] Invalid bbox values in {xml_path.name}, skipping object")
            continue

        # Clamp coordinates to image boundaries
        xmin = max(0.0, min(xmin, width))
        ymin = max(0.0, min(ymin, height))
        xmax = max(0.0, min(xmax, width))
        ymax = max(0.0, min(ymax, height))

        # Validate box has positive area
        if xmax <= xmin or ymax <= ymin:
            print(f"  [WARN] Degenerate bbox in {xml_path.name} (xmin={xmin}, xmax={xmax}, ymin={ymin}, ymax={ymax}), skipping object")
            continue

        # Convert to YOLO normalized format
        x_center = ((xmin + xmax) / 2.0) / width
        y_center = ((ymin + ymax) / 2.0) / height
        box_w    = (xmax - xmin) / width
        box_h    = (ymax - ymin) / height

        # Final validation: all values must be in [0, 1]
        if not (0.0 <= x_center <= 1.0 and 0.0 <= y_center <= 1.0 and
                0.0 < box_w <= 1.0 and 0.0 < box_h <= 1.0):
            print(f"  [WARN] Out-of-range YOLO values in {xml_path.name}, skipping object")
            continue

        boxes.append({
            "class_id": 0,  # All plates → single class
            "x_center": x_center,
            "y_center": y_center,
            "width": box_w,
            "height": box_h,
            "original_label": obj.findtext("name", "unknown")
        })

    return {
        "filename": filename_elem.text.strip(),
        "width": width,
        "height": height,
        "boxes": boxes
    }


def find_image_for_xml(xml_path: Path, expected_filename: str) -> Path | None:
    """
    Locate the matching image file for an XML annotation.
    Handles mismatched extensions and common naming patterns.
    """
    parent = xml_path.parent

    # Try the exact filename from XML
    candidate = parent / expected_filename
    if candidate.exists():
        return candidate

    # Try using the XML stem with common image extensions
    xml_stem = xml_path.stem
    for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG", ".bmp"]:
        candidate = parent / (xml_stem + ext)
        if candidate.exists():
            return candidate

    # Try matching by partial stem (handle the ___suffix pattern)
    # XML might be "uuid___name.jpg.xml" → image is "uuid___name.jpg.jpeg"
    for f in parent.iterdir():
        if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"] and f.stem == xml_stem:
            return f

    return None


def compute_file_hash(filepath: Path) -> str:
    """Compute MD5 hash of file for deduplication."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def collect_all_annotations(source_dir: Path) -> list[dict]:
    """
    Walk all subdirectories and collect parsed XML annotations
    paired with their image paths.
    """
    results = []
    xml_count = 0
    skip_count = 0
    no_image_count = 0
    no_box_count = 0

    subdirs = ["google_images", "video_images"]

    # Also add all State-wise_OLX subdirs
    olx_dir = source_dir / "State-wise_OLX"
    if olx_dir.exists():
        for state_dir in sorted(olx_dir.iterdir()):
            if state_dir.is_dir():
                subdirs.append(f"State-wise_OLX/{state_dir.name}")

    for subdir_name in subdirs:
        subdir = source_dir / subdir_name
        if not subdir.exists():
            continue

        xml_files = sorted(subdir.glob("*.xml"))
        print(f"\n  Scanning {subdir_name}/: {len(xml_files)} XML files")

        for xml_path in xml_files:
            xml_count += 1
            parsed = parse_voc_xml(xml_path)

            if parsed is None:
                skip_count += 1
                continue

            if len(parsed["boxes"]) == 0:
                no_box_count += 1
                continue

            # Find the matching image
            image_path = find_image_for_xml(xml_path, parsed["filename"])
            if image_path is None:
                no_image_count += 1
                continue

            results.append({
                "xml_path": xml_path,
                "image_path": image_path,
                "parsed": parsed
            })

    print(f"\n  ── Collection Summary ──")
    print(f"  Total XMLs scanned:     {xml_count}")
    print(f"  Parse errors/skipped:   {skip_count}")
    print(f"  No bounding boxes:      {no_box_count}")
    print(f"  Missing images:         {no_image_count}")
    print(f"  Valid pairs collected:   {len(results)}")

    return results


def deduplicate_by_hash(entries: list[dict]) -> list[dict]:
    """Remove duplicate images (by content hash)."""
    seen_hashes = {}
    unique = []
    dup_count = 0

    for entry in entries:
        file_hash = compute_file_hash(entry["image_path"])
        if file_hash not in seen_hashes:
            seen_hashes[file_hash] = entry["image_path"]
            unique.append(entry)
        else:
            dup_count += 1

    if dup_count > 0:
        print(f"  Removed {dup_count} duplicate images (by content hash)")

    return unique


def split_dataset(entries: list[dict], seed: int = 42) -> dict:
    """Split entries into train/valid/test sets."""
    random.seed(seed)
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
    """Write YOLO-formatted labels and copy images to output directory."""
    total_labels = 0
    total_boxes = 0
    label_stats = defaultdict(int)

    for split_name, entries in splits.items():
        img_dir = output_dir / split_name / "images"
        lbl_dir = output_dir / split_name / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for entry in entries:
            image_path = entry["image_path"]
            parsed = entry["parsed"]

            # Standardize image filename (use consistent naming)
            img_dest = img_dir / image_path.name
            lbl_dest = lbl_dir / (image_path.stem + ".txt")

            # Copy image
            if not img_dest.exists():
                shutil.copy2(str(image_path), str(img_dest))

            # Write YOLO label
            lines = []
            for box in parsed["boxes"]:
                line = f"{box['class_id']} {box['x_center']:.6f} {box['y_center']:.6f} {box['width']:.6f} {box['height']:.6f}"
                lines.append(line)
                total_boxes += 1
                label_stats[box["original_label"]] += 1

            with open(lbl_dest, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            total_labels += 1

    print(f"  Total label files written: {total_labels}")
    print(f"  Total bounding boxes:      {total_boxes}")
    print(f"  Unique plate texts seen:   {len(label_stats)}")


def write_data_yaml(output_dir: Path):
    """Generate data.yaml for YOLOv8 training."""
    yaml_content = f"""# Number Plate Detection — YOLOv8 Dataset Config
# Auto-generated by xml_to_yolo.py

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

        images = {f.stem for f in img_dir.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}}
        labels = {f.stem for f in lbl_dir.iterdir() if f.suffix == ".txt"}

        # Check for orphan labels (label without image)
        orphan_labels = labels - images
        if orphan_labels:
            print(f"  [WARN] {split}: {len(orphan_labels)} orphan labels (no matching image)")
            errors += 1

        # Check for missing labels (image without label)
        missing_labels = images - labels
        if missing_labels:
            print(f"  [WARN] {split}: {len(missing_labels)} images without labels")
            errors += 1

        # Validate YOLO format of sample labels
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
                        if cls_id != 0:
                            print(f"  [FAIL] {lbl_path.name}:{line_num} — class_id should be 0, got {cls_id}")
                            errors += 1
                        for v in vals:
                            if not (0.0 <= v <= 1.0):
                                print(f"  [FAIL] {lbl_path.name}:{line_num} — value {v} out of [0,1] range")
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
    print("║  XML → YOLO Converter (Number Plate)     ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Source: {SOURCE_DIR}")
    print(f"  Output: {OUTPUT_DIR}")

    if not SOURCE_DIR.exists():
        print(f"  [FATAL] Source directory does not exist: {SOURCE_DIR}")
        sys.exit(1)

    # Clean output directory
    if OUTPUT_DIR.exists():
        print(f"  Cleaning existing output directory...")
        shutil.rmtree(OUTPUT_DIR)

    # Step 1: Collect all annotations
    print("\n── Step 1: Collecting XML Annotations ──")
    entries = collect_all_annotations(SOURCE_DIR)

    if not entries:
        print("  [FATAL] No valid annotation pairs found!")
        sys.exit(1)

    # Step 2: Deduplicate
    print("\n── Step 2: Deduplicating ──")
    entries = deduplicate_by_hash(entries)

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
