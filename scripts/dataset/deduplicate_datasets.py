"""
Cross-Dataset Deduplication Script
====================================
Scans all datasets for duplicate images using MD5 hashing.
Duplicates are moved to a _duplicates/ backup folder (not deleted).
Matching label files for duplicates are also removed.

Datasets scanned:
  - datasets/detection/seat_belt/
  - datasets/detection/number_plate/ (source dirs)
  - datasets/detection/computer_vision/
  - datasets/detection/helmet/
  - datasets/classification/driver_behavior/
"""

import os
import sys
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = PROJECT_ROOT / "datasets"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

# Define datasets to scan with their structure
# Each entry: (name, base_dir, subdirs_with_images)
SCAN_TARGETS = [
    {
        "name": "seat_belt",
        "base": DATASETS_DIR / "detection" / "seat_belt",
        "image_dirs": ["train/images", "test/images", "valid/images"],
        "label_dirs": ["train/labels", "test/labels", "valid/labels"],
    },
    {
        "name": "computer_vision",
        "base": DATASETS_DIR / "detection" / "computer_vision",
        "image_dirs": ["train/images", "test/images", "valid/images"],
        "label_dirs": ["train/labels", "test/labels", "valid/labels"],
    },
    {
        "name": "helmet",
        "base": DATASETS_DIR / "detection" / "helmet",
        "image_dirs": ["train/images", "test/images", "valid/images"],
        "label_dirs": ["train/labels", "test/labels", "valid/labels"],
    },
    {
        "name": "driver_behavior",
        "base": DATASETS_DIR / "classification" / "driver_behavior",
        "image_dirs": ["train/images", "test/images", "valid/images"],
        "label_dirs": ["train/labels", "test/labels", "valid/labels"],
    },
]


def compute_md5(filepath: Path) -> str:
    """Compute MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_label_file(image_path: Path, label_dirs: list[Path]) -> Path | None:
    """
    Find the corresponding label file for an image.
    Checks all label directories for a matching .txt file.
    """
    stem = image_path.stem
    for lbl_dir in label_dirs:
        lbl_path = lbl_dir / f"{stem}.txt"
        if lbl_path.exists():
            return lbl_path
    return None


def scan_dataset(target: dict) -> dict:
    """
    Scan a single dataset for duplicate images.
    Returns stats dict.
    """
    name = target["name"]
    base = target["base"]

    print(f"\n  ── Scanning: {name} ──")
    print(f"     Base: {base}")

    if not base.exists():
        print(f"     [SKIP] Directory does not exist")
        return {"name": name, "total": 0, "duplicates": 0, "errors": 0}

    # Collect all image files from configured subdirs
    all_images = []
    for img_subdir in target["image_dirs"]:
        img_dir = base / img_subdir
        if img_dir.exists():
            images = [f for f in img_dir.iterdir()
                      if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
            all_images.extend(images)
            print(f"     {img_subdir}: {len(images)} images")

    # Also scan the base directory directly (for flat-structure datasets)
    if not all_images:
        # Try scanning base dir for images (flat structure)
        flat_images = [f for f in base.iterdir()
                       if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
        if flat_images:
            all_images.extend(flat_images)
            print(f"     (flat): {len(flat_images)} images")

    if not all_images:
        print(f"     No images found")
        return {"name": name, "total": 0, "duplicates": 0, "errors": 0}

    # Collect label directories
    label_dirs = []
    for lbl_subdir in target.get("label_dirs", []):
        lbl_dir = base / lbl_subdir
        if lbl_dir.exists():
            label_dirs.append(lbl_dir)

    # Create backup directory for duplicates
    backup_dir = base / "_duplicates"

    # Hash all images and find duplicates
    hash_to_first = {}  # hash → first seen image path
    duplicates = []
    errors = 0

    for img_path in sorted(all_images):
        try:
            file_hash = compute_md5(img_path)
        except (OSError, IOError) as e:
            print(f"     [ERROR] Cannot read {img_path.name}: {e}")
            errors += 1
            continue

        if file_hash in hash_to_first:
            duplicates.append((img_path, hash_to_first[file_hash]))
        else:
            hash_to_first[file_hash] = img_path

    # Move duplicates to backup
    if duplicates:
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"     Found {len(duplicates)} duplicates")

        for dup_path, original_path in duplicates:
            # Move duplicate image to backup
            backup_dest = backup_dir / dup_path.name
            counter = 1
            while backup_dest.exists():
                backup_dest = backup_dir / f"{dup_path.stem}_dup{counter}{dup_path.suffix}"
                counter += 1

            try:
                shutil.move(str(dup_path), str(backup_dest))
            except (OSError, IOError) as e:
                print(f"     [ERROR] Cannot move {dup_path.name}: {e}")
                errors += 1
                continue

            # Remove matching label file
            lbl_path = find_label_file(dup_path, label_dirs)
            if lbl_path and lbl_path.exists():
                try:
                    lbl_path.unlink()
                except OSError:
                    pass

    else:
        print(f"     No duplicates found ✓")

    stats = {
        "name": name,
        "total": len(all_images),
        "duplicates": len(duplicates),
        "remaining": len(all_images) - len(duplicates),
        "errors": errors,
    }

    return stats


def scan_number_plate_source(datasets_dir: Path) -> dict:
    """
    Special handler for number_plate dataset which has a non-standard structure.
    Images and XMLs are mixed together in subdirectories.
    """
    name = "number_plate (source)"
    base = datasets_dir / "detection" / "number_plate"

    print(f"\n  ── Scanning: {name} ──")
    print(f"     Base: {base}")

    if not base.exists():
        return {"name": name, "total": 0, "duplicates": 0, "errors": 0}

    # Collect all images from all subdirs
    all_images = []
    for subdir in ["google_images", "video_images"]:
        img_dir = base / subdir
        if img_dir.exists():
            images = [f for f in img_dir.iterdir()
                      if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
            all_images.extend(images)
            print(f"     {subdir}: {len(images)} images")

    # State-wise_OLX subdirs
    olx_dir = base / "State-wise_OLX"
    if olx_dir.exists():
        olx_count = 0
        for state_dir in olx_dir.iterdir():
            if state_dir.is_dir():
                images = [f for f in state_dir.iterdir()
                          if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
                all_images.extend(images)
                olx_count += len(images)
        print(f"     State-wise_OLX (all states): {olx_count} images")

    if not all_images:
        print(f"     No images found")
        return {"name": name, "total": 0, "duplicates": 0, "errors": 0}

    backup_dir = base / "_duplicates"

    # Hash and find duplicates
    hash_to_first = {}
    duplicates = []
    errors = 0

    for img_path in sorted(all_images):
        try:
            file_hash = compute_md5(img_path)
        except (OSError, IOError) as e:
            errors += 1
            continue

        if file_hash in hash_to_first:
            duplicates.append((img_path, hash_to_first[file_hash]))
        else:
            hash_to_first[file_hash] = img_path

    if duplicates:
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"     Found {len(duplicates)} duplicates")

        for dup_path, _ in duplicates:
            backup_dest = backup_dir / dup_path.name
            counter = 1
            while backup_dest.exists():
                backup_dest = backup_dir / f"{dup_path.stem}_dup{counter}{dup_path.suffix}"
                counter += 1

            try:
                shutil.move(str(dup_path), str(backup_dest))
            except (OSError, IOError):
                errors += 1
                continue

            # Remove matching XML
            xml_path = dup_path.with_suffix(".xml")
            if xml_path.exists():
                try:
                    xml_path.unlink()
                except OSError:
                    pass
    else:
        print(f"     No duplicates found ✓")

    return {
        "name": name,
        "total": len(all_images),
        "duplicates": len(duplicates),
        "remaining": len(all_images) - len(duplicates),
        "errors": errors,
    }


def main():
    print("╔══════════════════════════════════════════╗")
    print("║  Cross-Dataset Deduplication             ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Datasets root: {DATASETS_DIR}")

    all_stats = []

    # Scan standard datasets
    for target in SCAN_TARGETS:
        stats = scan_dataset(target)
        all_stats.append(stats)

    # Scan number_plate (special structure)
    stats = scan_number_plate_source(DATASETS_DIR)
    all_stats.append(stats)

    # Print summary table
    print("\n══════════════════════════════════════════")
    print("  DEDUPLICATION SUMMARY")
    print("══════════════════════════════════════════")
    print(f"  {'Dataset':<30s} {'Total':>8s} {'Dupes':>8s} {'Remaining':>10s} {'Errors':>8s}")
    print(f"  {'─'*30} {'─'*8} {'─'*8} {'─'*10} {'─'*8}")

    total_images = 0
    total_dupes = 0
    total_errors = 0

    for stats in all_stats:
        total_images += stats["total"]
        total_dupes  += stats["duplicates"]
        total_errors += stats.get("errors", 0)

        remaining = stats.get("remaining", stats["total"] - stats["duplicates"])
        print(f"  {stats['name']:<30s} {stats['total']:>8,d} {stats['duplicates']:>8,d} {remaining:>10,d} {stats.get('errors', 0):>8,d}")

    print(f"  {'─'*30} {'─'*8} {'─'*8} {'─'*10} {'─'*8}")
    print(f"  {'TOTAL':<30s} {total_images:>8,d} {total_dupes:>8,d} {total_images - total_dupes:>10,d} {total_errors:>8,d}")

    if total_dupes > 0:
        print(f"\n  📁 Duplicates backed up to _duplicates/ folders (not permanently deleted)")
    
    print("\n══════════════════════════════════════════")
    print("  DEDUPLICATION COMPLETE ✓")
    print("══════════════════════════════════════════")


if __name__ == "__main__":
    main()
