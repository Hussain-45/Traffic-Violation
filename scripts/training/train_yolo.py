"""
YOLOv8 Training Script — Smart Traffic Violation Detection System (STVDS)
========================================================================
Automates custom fine-tuning of YOLOv8 object detection models on the datasets
prepared in Phase 1.

Usage:
  python train_yolo.py --dataset [helmet|seat_belt|number_plate|computer_vision|traffic_light]
                       [--epochs 50] [--batch 16] [--imgsz 640] [--device cpu|0]

Weights Output:
  models/trained/[dataset]_best.pt
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
PRETRAINED_DIR = MODELS_DIR / "pretrained"
TRAINED_DIR = MODELS_DIR / "trained"

# Map datasets to their data.yaml locations
DATASETS_MAP = {
    "helmet": PROJECT_ROOT / "datasets" / "detection" / "helmet" / "data.yaml",
    "seat_belt": PROJECT_ROOT / "datasets" / "detection" / "seat_belt" / "data.yaml",
    "number_plate": PROJECT_ROOT / "datasets" / "detection" / "number_plate_yolo" / "data.yaml",
    "computer_vision": PROJECT_ROOT / "datasets" / "detection" / "computer_vision" / "data.yaml",
    "traffic_light": PROJECT_ROOT / "datasets" / "detection" / "traffic_light_yolo" / "data.yaml",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Train custom YOLOv8 model for STVDS.")
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        choices=list(DATASETS_MAP.keys()),
        help="Dataset name to train model on."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs."
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size."
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size."
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Device to train on (e.g. cpu, 0, 1, or auto)."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0 if os.name == "nt" else 8,
        help="Number of dataloader workers."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("╔══════════════════════════════════════════╗")
    print("║  YOLOv8 Custom Model Trainer (STVDS)     ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Dataset:     {args.dataset}")
    print(f"  Epochs:      {args.epochs}")
    print(f"  Batch size:  {args.batch}")
    print(f"  Image size:  {args.imgsz}")

    # Ensure output folders exist
    PRETRAINED_DIR.mkdir(parents=True, exist_ok=True)
    TRAINED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Resolve dataset config path
    data_yaml_path = DATASETS_MAP[args.dataset]
    if not data_yaml_path.exists():
        print(f"  [FATAL] data.yaml not found at: {data_yaml_path}")
        print("  Please make sure you have run the Phase 1 scripts first.")
        sys.exit(1)

    print(f"  Data Config: {data_yaml_path}")

    # 2. Resolve pretrained base model path
    base_model_path = PRETRAINED_DIR / "yolov8n.pt"
    if not base_model_path.exists():
        print(f"\n  Base model yolov8n.pt not found in {PRETRAINED_DIR}.")
        print("  It will be downloaded automatically during startup.")
    else:
        print(f"  Base Model:  {base_model_path}")

    # 3. Initialize YOLOv8 and train
    try:
        from ultralytics import YOLO
    except ImportError:
        print("\n  [FATAL] Ultralytics package is not installed.")
        print("  Please run scripts/setup/setup_training_env.ps1 first.")
        sys.exit(1)

    # Set device
    device = args.device
    if device == "auto":
        import torch
        device = "0" if torch.cuda.is_available() else "cpu"
    print(f"  Training on: {device}")

    # Initialize model
    model = YOLO(str(base_model_path) if base_model_path.exists() else "yolov8n.pt")

    # Start training run
    print("\n── Starting Ultralytics Training Run ──")
    project_name = f"stvds_{args.dataset}_run"
    
    results = model.train(
        data=str(data_yaml_path),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=device,
        project=project_name,
        name="train_results",
        exist_ok=True,
        workers=args.workers
    )

    # 4. Extract and copy weights
    print("\n── Processing Completed Run Weights ──")
    run_dir = Path(project_name) / "train_results"
    best_weights = run_dir / "weights" / "best.pt"

    # Alternate check if runs were saved to default yolov8 runs/ directory
    if not best_weights.exists():
        best_weights = Path("runs") / "detect" / "train_results" / "weights" / "best.pt"
        if not best_weights.exists():
            # Search recursively for best.pt in case of name increments
            search_pattern = "**/weights/best.pt"
            found_runs = list(Path().glob(search_pattern))
            if found_runs:
                # Get the most recently modified runs weight file
                found_runs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                best_weights = found_runs[0]

    if best_weights.exists():
        dest_weights_path = TRAINED_DIR / f"{args.dataset}_best.pt"
        shutil.copy2(str(best_weights), str(dest_weights_path))
        print(f"  ✅ Copying weights: {best_weights} → {dest_weights_path}")
        
        # Clean up local run dir if created in root to keep repo clean
        # (leave runs/ directory alone as user logs)
        if Path(project_name).exists():
            print(f"  Cleaning temporary run directory: {project_name}")
            shutil.rmtree(project_name)
    else:
        print(f"  [ERROR] best.pt weight file not found. Training may have failed.")
        sys.exit(1)

    print("\n══════════════════════════════════════════")
    print(f"  TRAINING COMPLETE FOR: {args.dataset.upper()} ✓")
    print("══════════════════════════════════════════")


if __name__ == "__main__":
    main()
