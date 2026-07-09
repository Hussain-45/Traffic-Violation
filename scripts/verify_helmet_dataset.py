import os
import yaml
from collections import Counter

dataset_dir = "datasets/detection/helmet"
splits = ["train", "valid", "test"]

stats = {}

for split in splits:
    img_dir = os.path.join(dataset_dir, split, "images")
    lbl_dir = os.path.join(dataset_dir, split, "labels")
    
    if not os.path.exists(img_dir):
        print(f"Directory {img_dir} does not exist.")
        continue
    
    images = [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
    labels = [f for f in os.listdir(lbl_dir) if f.lower().endswith('.txt')] if os.path.exists(lbl_dir) else []
    
    # Analyze classes in labels
    classes = []
    for lbl in labels:
        lbl_path = os.path.join(lbl_dir, lbl)
        with open(lbl_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    classes.append(parts[0])
                    
    class_counts = dict(Counter(classes))
    
    stats[split] = {
        "images": len(images),
        "labels": len(labels),
        "annotations_total": len(classes),
        "class_distribution": class_counts
    }

print("Dataset Statistics:")
print(yaml.dump(stats))
