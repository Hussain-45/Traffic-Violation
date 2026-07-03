import os
import sys
from PIL import Image

def preprocess_dataset(src_dir, dest_dir, prefix="img"):
    print(f"Preprocessing dataset: {src_dir} -> {dest_dir}")
    src_images_dir = os.path.join(src_dir, "images")
    src_labels_dir = os.path.join(src_dir, "labels")

    dest_images_dir = os.path.join(dest_dir, "images")
    dest_labels_dir = os.path.join(dest_dir, "labels")

    os.makedirs(dest_images_dir, exist_ok=True)
    os.makedirs(dest_labels_dir, exist_ok=True)

    if not os.path.exists(src_images_dir) or not os.path.exists(src_labels_dir):
        print(f"Error: Missing images or labels directory under {src_dir}")
        return False

    image_files = [f for f in os.listdir(src_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    processed_count = 0
    skipped_count = 0

    for idx, img_name in enumerate(image_files):
        base_name, ext = os.path.splitext(img_name)
        lbl_name = f"{base_name}.txt"
        lbl_path = os.path.join(src_labels_dir, lbl_name)

        if not os.path.exists(lbl_path):
            skipped_count += 1
            continue

        src_img_path = os.path.join(src_images_dir, img_name)
        
        # 1. Image loading and resizing to 640x640
        try:
            with Image.open(src_img_path) as img:
                img_resized = img.resize((640, 640), Image.Resampling.LANCZOS)
                
                # Convert RGBA to RGB if needed (JPEG does not support alpha channel)
                if img_resized.mode == 'RGBA':
                    img_resized = img_resized.convert('RGB')
                
                new_img_name = f"{prefix}_{idx:05d}.jpg"
                dest_img_path = os.path.join(dest_images_dir, new_img_name)
                img_resized.save(dest_img_path, "JPEG", quality=90)
        except Exception as e:
            print(f"Skipping corrupt image: {img_name} due to: {e}")
            skipped_count += 1
            continue

        # 2. Label preprocessing and cleaning
        dest_lbl_name = f"{prefix}_{idx:05d}.txt"
        dest_lbl_path = os.path.join(dest_labels_dir, dest_lbl_name)

        try:
            with open(lbl_path, "r") as f:
                lines = f.readlines()

            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 5:
                    continue
                
                try:
                    cls_id = int(parts[0])
                    coords = [float(x) for x in parts[1:]]
                    # Ensure within normalized bounds
                    coords_bounded = [max(0.0, min(1.0, c)) for c in coords]
                    line_str = f"{cls_id} " + " ".join(f"{c:.6f}" for c in coords_bounded)
                    cleaned_lines.append(line_str)
                except ValueError:
                    continue

            with open(dest_lbl_path, "w") as f:
                f.write("\n".join(cleaned_lines) + "\n")

            processed_count += 1
        except Exception as e:
            print(f"Failed to process label {lbl_name}: {e}")
            skipped_count += 1

    print(f"Finished preprocessing. Successfully processed: {processed_count}, Skipped/Corrupt: {skipped_count}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 2:
        preprocess_dataset(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python preprocessing.py <src_directory> <dest_directory> [prefix]")
