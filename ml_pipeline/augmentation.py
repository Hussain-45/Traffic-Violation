import os
import sys
import random
from PIL import Image, ImageEnhance, ImageFilter

# Try to import albumentations
try:
    import albumentations as A
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False
    print("Warning: albumentations library not found. Falling back to PIL-based data augmentation.")

def get_albumentations_pipeline():
    return A.Compose([
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.4),
        A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=20, val_shift_limit=15, p=0.4),
        A.ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.1, rotate_limit=15, p=0.3),
        A.Blur(blur_limit=3, p=0.2),
    ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

def augment_image_pil(img_path, lbl_path, dest_img_path, dest_lbl_path):
    # PIL Fallback augmentation (Horizontal Flip)
    try:
        with Image.open(img_path) as img:
            # 1. Random Flip
            do_flip = random.random() > 0.5
            if do_flip:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            
            # 2. Brightness adjustment
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(random.uniform(0.8, 1.2))

            # 3. Blur
            if random.random() > 0.8:
                img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.5)))

            img.save(dest_img_path, "JPEG")

        # Adjust bounding boxes if flipped
        with open(lbl_path, "r") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            cls_id = parts[0]
            x_center = float(parts[1])
            y_center = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])

            if do_flip:
                x_center = 1.0 - x_center

            new_lines.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")

        with open(dest_lbl_path, "w") as f:
            f.write("\n".join(new_lines) + "\n")

    except Exception as e:
        print(f"PIL Augmentation failed for {img_path}: {e}")

def augment_dataset(unified_dataset_dir, num_augments_per_image=1):
    print(f"Running data augmentation on training set in: {unified_dataset_dir}")
    train_images_dir = os.path.join(unified_dataset_dir, "images", "train")
    train_labels_dir = os.path.join(unified_dataset_dir, "labels", "train")

    if not os.path.exists(train_images_dir):
        print("Error: Train images folder not found!")
        return False

    image_files = [f for f in os.listdir(train_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Found {len(image_files)} training images to augment.")

    pipeline = get_albumentations_pipeline() if ALBUMENTATIONS_AVAILABLE else None
    augmented_count = 0

    for img_name in image_files:
        base_name, ext = os.path.splitext(img_name)
        lbl_name = f"{base_name}.txt"
        img_path = os.path.join(train_images_dir, img_name)
        lbl_path = os.path.join(train_labels_dir, lbl_name)

        if not os.path.exists(lbl_path):
            continue

        for i in range(num_augments_per_image):
            aug_img_name = f"{base_name}_aug{i}{ext}"
            aug_lbl_name = f"{base_name}_aug{i}.txt"

            dest_img_path = os.path.join(train_images_dir, aug_img_name)
            dest_lbl_path = os.path.join(train_labels_dir, aug_lbl_name)

            if ALBUMENTATIONS_AVAILABLE:
                try:
                    import cv2
                    image = cv2.imread(img_path)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                    # Read labels
                    bboxes = []
                    class_labels = []
                    with open(lbl_path, "r") as f:
                        for line in f.readlines():
                            parts = line.strip().split()
                            if len(parts) != 5:
                                continue
                            cls_id = int(parts[0])
                            bbox = [float(x) for x in parts[1:]]
                            # Bbox coordinates check
                            if bbox[2] <= 0 or bbox[3] <= 0:
                                continue
                            # Clamp bounding boxes slightly inside frame boundary for safety
                            bbox[0] = max(0.01, min(0.99, bbox[0]))
                            bbox[1] = max(0.01, min(0.99, bbox[1]))
                            bbox[2] = max(0.01, min(0.99, bbox[2]))
                            bbox[3] = max(0.01, min(0.99, bbox[3]))
                            bboxes.append(bbox)
                            class_labels.append(cls_id)

                    if not bboxes:
                        # Skip image if no bboxes exist
                        continue

                    transformed = pipeline(image=image, bboxes=bboxes, class_labels=class_labels)
                    transformed_image = transformed['image']
                    transformed_bboxes = transformed['bboxes']
                    transformed_classes = transformed['class_labels']

                    # Save augmented image
                    transformed_image_pil = Image.fromarray(transformed_image)
                    transformed_image_pil.save(dest_img_path)

                    # Save augmented labels
                    with open(dest_lbl_path, "w") as f:
                        for bbox, cls_id in zip(transformed_bboxes, transformed_classes):
                            f.write(f"{cls_id} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")

                    augmented_count += 1
                except Exception as e:
                    # Fallback to PIL if Albumentations fails
                    augment_image_pil(img_path, lbl_path, dest_img_path, dest_lbl_path)
                    augmented_count += 1
            else:
                augment_image_pil(img_path, lbl_path, dest_img_path, dest_lbl_path)
                augmented_count += 1

    print(f"Data augmentation completed! Generated {augmented_count} augmented files.")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        augment_dataset(sys.argv[1])
    else:
        print("Usage: python augmentation.py <unified_dataset_dir>")
