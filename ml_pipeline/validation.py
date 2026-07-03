import os
import sys
import hashlib
from PIL import Image
from collections import Counter

def validate_dataset(data_dir, output_report_path):
    print(f"Validating dataset directory: {data_dir}")
    images_dir = os.path.join(data_dir, "images")
    labels_dir = os.path.join(data_dir, "labels")

    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)

    report_lines = []
    report_lines.append(f"# Validation Report for {os.path.basename(data_dir)}")
    report_lines.append(f"Directory: {data_dir}\n")

    if not os.path.exists(images_dir) or not os.path.exists(labels_dir):
        report_lines.append("ERROR: 'images' or 'labels' subdirectory does not exist!")
        with open(output_report_path, "w") as f:
            f.write("\n".join(report_lines))
        return False

    image_files = {os.path.splitext(f)[0]: f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))}
    label_files = {os.path.splitext(f)[0]: f for f in os.listdir(labels_dir) if f.lower().endswith('.txt')}

    all_keys = set(image_files.keys()).union(set(label_files.keys()))

    corrupt_images = []
    duplicate_hashes = {}
    duplicates_found = []
    invalid_annotations = []
    class_counter = Counter()
    missing_labels = []
    missing_images = []

    for key in all_keys:
        img_name = image_files.get(key)
        lbl_name = label_files.get(key)

        # 1. Missing files checks
        if img_name and not lbl_name:
            missing_labels.append(img_name)
        elif lbl_name and not img_name:
            missing_images.append(lbl_name)

        # 2. Image integrity checks
        if img_name:
            img_path = os.path.join(images_dir, img_name)
            
            # Corrupt check
            try:
                with Image.open(img_path) as img:
                    img.verify()
            except Exception as e:
                corrupt_images.append((img_name, str(e)))
                continue

            # Duplicate check using MD5 hash
            try:
                hasher = hashlib.md5()
                with open(img_path, 'rb') as f:
                    buf = f.read()
                    hasher.update(buf)
                img_hash = hasher.hexdigest()
                if img_hash in duplicate_hashes:
                    duplicates_found.append((img_name, duplicate_hashes[img_hash]))
                else:
                    duplicate_hashes[img_hash] = img_name
            except Exception as e:
                pass

        # 3. Label annotations validation
        if lbl_name:
            lbl_path = os.path.join(labels_dir, lbl_name)
            try:
                with open(lbl_path, "r") as f:
                    lines = f.readlines()
                
                for idx, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) != 5:
                        invalid_annotations.append((lbl_name, f"Line {idx+1}: Expected 5 elements, got {len(parts)}"))
                        continue
                    
                    try:
                        cls_id = int(parts[0])
                        coords = [float(x) for x in parts[1:]]
                    except ValueError:
                        invalid_annotations.append((lbl_name, f"Line {idx+1}: Coordinates must be numeric"))
                        continue
                    
                    # YOLO coordinate bounds check (x, y, w, h must be between 0 and 1)
                    if any(c < 0.0 or c > 1.0 for c in coords):
                        invalid_annotations.append((lbl_name, f"Line {idx+1}: Normalized coordinates {coords} out of bounds [0, 1]"))
                    
                    class_counter[cls_id] += 1
            except Exception as e:
                invalid_annotations.append((lbl_name, f"Read error: {str(e)}"))

    # Compilation of Report metrics
    report_lines.append(f"## Dataset Statistics")
    report_lines.append(f"- Total Images: {len(image_files)}")
    report_lines.append(f"- Total Label Files: {len(label_files)}")
    report_lines.append(f"- Images without labels: {len(missing_labels)}")
    report_lines.append(f"- Labels without images: {len(missing_images)}")
    report_lines.append(f"- Corrupt images detected: {len(corrupt_images)}")
    report_lines.append(f"- Duplicate images detected: {len(duplicates_found)}")
    report_lines.append(f"- Invalid annotations detected: {len(invalid_annotations)}\n")

    report_lines.append("## Class Distribution")
    if class_counter:
        for cls_id, count in sorted(class_counter.items()):
            report_lines.append(f"- Class ID {cls_id}: {count} annotations")
    else:
        report_lines.append("- No annotations found.")
    report_lines.append("")

    if missing_labels:
        report_lines.append("## Images Missing Labels (First 10)")
        for name in missing_labels[:10]:
            report_lines.append(f"- {name}")
        report_lines.append("")

    if corrupt_images:
        report_lines.append("## Corrupt Images")
        for name, err in corrupt_images[:10]:
            report_lines.append(f"- {name}: {err}")
        report_lines.append("")

    if duplicates_found:
        report_lines.append("## Duplicate Images (First 10)")
        for duplicate, original in duplicates_found[:10]:
            report_lines.append(f"- {duplicate} is a duplicate of {original}")
        report_lines.append("")

    if invalid_annotations:
        report_lines.append("## Invalid YOLO Annotations (First 10)")
        for name, err in invalid_annotations[:10]:
            report_lines.append(f"- {name}: {err}")
        report_lines.append("")

    # Write report file
    with open(output_report_path, "w") as f:
        f.write("\n".join(report_lines))

    print(f"Validation report saved to: {output_report_path}")
    return len(corrupt_images) == 0 and len(invalid_annotations) == 0

if __name__ == "__main__":
    # Test script if executed directly
    if len(sys.argv) > 1:
        validate_dataset(sys.argv[1], "data/validation_reports/test_report.txt")
    else:
        print("Usage: python validation.py <dataset_directory>")
