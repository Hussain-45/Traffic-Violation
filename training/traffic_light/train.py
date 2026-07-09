"""
Traffic Light Model Training Script
===================================
Provides a reusable training pipeline for custom YOLOv8 traffic light models.

Supports:
  1. Resume training from checkpoints/last.pt
  2. Early stopping via patience parameter
  3. Best model saving and weights export (ONNX/Engine)
  4. Dynamic model size selection
  5. Configurable epochs, batch size, and image size
"""
import os
import sys
import argparse
import shutil
from pathlib import Path
from loguru import logger

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAINING_DIR = PROJECT_ROOT / "training" / "traffic_light"
DATASET_YAML = PROJECT_ROOT / "datasets" / "detection" / "traffic_light_yolo" / "data.yaml"
OUTPUT_BEST_DIR = PROJECT_ROOT / "models" / "trained"


def setup_training_directories():
    """Create the required training folder structure if it doesn't exist."""
    folders = ["configs", "weights", "runs", "results", "logs", "exports", "checkpoints"]
    for folder in folders:
        path = TRAINING_DIR / folder
        path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Training directories initialized under: {TRAINING_DIR}")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Train custom YOLOv8 model for Traffic Signal Detection.")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size")
    parser.add_argument("--device", type=str, default="auto", help="Device to train on (cpu, cuda, or 0, 1 etc.)")
    parser.add_argument("--patience", type=int, default=10, help="Epoch patience for early stopping")
    parser.add_argument("--model-size", type=str, default="n", choices=["n", "s", "m", "l", "x"], 
                        help="YOLOv8 model size (n=nano, s=small, m=medium, l=large, x=extra-large)")
    parser.add_argument("--resume", action="store_true", help="Resume training from checkpoints/last.pt")
    parser.add_argument("--export", type=str, choices=["onnx", "engine"], default=None, 
                        help="Export best model format after training")
    return parser.parse_args()


def run_training():
    args = parse_arguments()
    setup_training_directories()
    
    # 1. Validate dataset existence
    if not DATASET_YAML.exists():
        logger.error(f"Dataset data.yaml not found at: {DATASET_YAML}")
        logger.error("Verify datasets/detection/traffic_light_yolo directory is populated.")
        sys.exit(1)
        
    logger.info(f"Using dataset configuration: {DATASET_YAML}")
    
    # 2. Check for last checkpoint or dynamic model initialization
    checkpoint_last = TRAINING_DIR / "checkpoints" / "last.pt"
    if args.resume and checkpoint_last.exists():
        model_path = str(checkpoint_last)
        logger.info(f"Resuming training from last checkpoint: {model_path}")
    else:
        if args.resume:
            logger.warning(f"Resume requested but last checkpoint {checkpoint_last} not found. Starting fresh.")
        model_path = f"yolov8{args.model_size}.pt"
        logger.info(f"Initializing fresh YOLOv8 model: {model_path}")
        
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.critical("Ultralytics package is not installed. Run 'pip install ultralytics'.")
        sys.exit(1)
        
    model = YOLO(model_path)
    
    # Resolve hardware device
    device = args.device
    if device == "auto":
        import torch
        device = "0" if torch.cuda.is_available() else "cpu"
    logger.info(f"Executing training on device: {device}")
    
    # Start training
    logger.info("Starting Ultralytics training run for Traffic Lights...")
    results = model.train(
        data=str(DATASET_YAML),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=device,
        patience=args.patience,
        project=str(TRAINING_DIR / "runs"),
        name="traffic_run",
        exist_ok=True,
        resume=args.resume,
        plots=True
    )
    
    logger.info("Training completed.")
    
    # Resolve and copy checkpoints/best weights
    best_weights = TRAINING_DIR / "runs" / "traffic_run" / "weights" / "best.pt"
    last_weights = TRAINING_DIR / "runs" / "traffic_run" / "weights" / "last.pt"
    
    if best_weights.exists():
        # Save to training/traffic_light/weights
        dest_best = TRAINING_DIR / "weights" / f"traffic_{args.model_size}_best.pt"
        shutil.copy2(best_weights, dest_best)
        logger.info(f"Copied best weights to: {dest_best}")
        
        # Copy to central models directory
        OUTPUT_BEST_DIR.mkdir(parents=True, exist_ok=True)
        central_best = OUTPUT_BEST_DIR / "traffic_light_best.pt"
        shutil.copy2(best_weights, central_best)
        logger.info(f"Copied best weights to central registry: {central_best}")
        
        # Handle exports
        if args.export:
            logger.info(f"Exporting model to {args.export} format...")
            export_model = YOLO(str(dest_best))
            export_path = export_model.export(format=args.export)
            logger.info(f"Model exported successfully: {export_path}")
            
            # Copy to exports folder
            dest_export = TRAINING_DIR / "exports" / Path(export_path).name
            shutil.copy2(export_path, dest_export)
            logger.info(f"Saved exported model to: {dest_export}")
    else:
        logger.error("Could not find best.pt. Training run might have failed.")
        
    if last_weights.exists():
        # Copy to checkpoints/ for resume support
        dest_last = TRAINING_DIR / "checkpoints" / "last.pt"
        shutil.copy2(last_weights, dest_last)
        logger.info(f"Saved last weights checkpoint to: {dest_last}")


if __name__ == "__main__":
    run_training()
