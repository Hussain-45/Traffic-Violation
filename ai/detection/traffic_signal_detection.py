"""
Traffic Signal Detection AI Module
==================================
Executes YOLOv8 traffic light state classification, uses central RoadSceneService
to target traffic light ROIs, resolves lit states, and draws annotated overlays.
"""
import os
import cv2
import yaml
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from loguru import logger
from ultralytics import YOLO

from ai.pipelines.base_module import BaseAIModule
from ai.pipelines.pipeline_context import PipelineContext
from ai.services.road_scene_service import RoadSceneService
from shared.schemas import DetectionResult


class TrafficSignalDetectionModule(BaseAIModule):
    """
    YOLOv8-based Traffic Signal Detection Module.
    Validates signal lit states (Red, Yellow, Green, Unknown) inside the traffic light ROI.
    """

    def __init__(self, models_config_path: str = "configs/models.yaml"):
        self.models_config_path = models_config_path
        self.model: Optional[YOLO] = None
        self.weights_path: Optional[str] = None
        self.active_size: str = "n"
        self._initialized = False

    def initialize(self) -> None:
        """Load configuration and initialize YOLO model weights."""
        if self._initialized:
            return

        # 1. Resolve weights path from models.yaml
        if os.path.exists(self.models_config_path):
            try:
                with open(self.models_config_path, "r") as f:
                    cfg = yaml.safe_load(f) or {}
                ts_cfg = cfg.get("traffic_signal", {})
                self.active_size = ts_cfg.get("active_size", "n")
                sizes = ts_cfg.get("sizes", {})
                self.weights_path = sizes.get(self.active_size, {}).get("weights")
                logger.info(f"Traffic Signal model size configured: '{self.active_size}' with weights '{self.weights_path}'")
            except Exception as e:
                logger.error(f"Error parsing {self.models_config_path}: {e}. Using default weights.")
                self.weights_path = "models/trained/traffic_light_best.pt"
        else:
            logger.warning(f"{self.models_config_path} not found. Using default weights path.")
            self.weights_path = "models/trained/traffic_light_best.pt"

        # 2. Check weights existence and load model
        if not self.weights_path or not os.path.exists(self.weights_path):
            logger.warning(f"Traffic Signal weights not found at '{self.weights_path}'. Traffic Signal detection will run in Mock/Disabled mode.")
            self.model = None
        else:
            try:
                logger.info(f"Loading Traffic Signal Detection model from '{self.weights_path}'...")
                self.model = YOLO(self.weights_path)
                logger.info("Traffic Signal model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Traffic Signal model: {e}")
                self.model = None

        self._initialized = True

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processes the frame, matches traffic light detections to ROI,
        and annotates overlays on working_frame.
        """
        errors = []
        warnings = []
        results = {
            "red_count": 0,
            "yellow_count": 0,
            "green_count": 0,
            "unknown_count": 0,
            "status": "Inactive"
        }

        # 1. Check if model is loaded
        if self.model is None:
            msg = "Traffic Signal model not trained / weights missing"
            context.add_warning("traffic_signal_detection", msg)
            warnings.append({"module": "traffic_signal_detection", "message": msg})
            return results, errors, warnings

        results["status"] = "Active"

        try:
            # Get confidence threshold from pipeline context config
            conf_threshold = context.config.get("traffic_signal_detection", {}).get("confidence_threshold", 0.50)

            # 2. Run model on full frame
            model_results = self.model(frame, verbose=False)
            if not model_results:
                return results, errors, warnings

            detections = model_results[0].boxes
            
            # Fetch Traffic Light ROI boundaries
            f_h, f_w = frame.shape[:2]
            traffic_light_roi = RoadSceneService.get_traffic_light_roi(f_w, f_h)

            # 3. Filter detections inside the ROI and sort horizontally (left to right) to generate stable signal IDs
            raw_dets = []
            for box in detections:
                cls_idx = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                if conf < conf_threshold:
                    continue
                xyxy = box.xyxy[0].tolist()
                
                # Check if center is in Traffic Light ROI
                if RoadSceneService.is_in_roi(xyxy, traffic_light_roi):
                    raw_dets.append({
                        "cls": cls_idx,
                        "conf": conf,
                        "xyxy": xyxy
                    })

            # Sort horizontally by x1 coordinate
            raw_dets.sort(key=lambda d: d["xyxy"][0])

            traffic_signal_stats = {}

            # Map classes: 0=red, 1=green, 2=yellow, 3=unknown, 4=traffic_light
            class_to_status = {
                0: "Red",
                1: "Green",
                2: "Yellow",
                3: "Unknown",
                4: "Unknown"
            }

            for idx, det in enumerate(raw_dets):
                signal_id = idx + 1
                status_val = class_to_status.get(det["cls"], "Unknown")
                conf_val = det["conf"]
                
                det_res = DetectionResult(
                    module_name="traffic_signal_detection",
                    signal_id=signal_id,
                    tracking_id=None,  # Nullable track ID
                    vehicle_class=-1,
                    region=det["xyxy"],
                    status=status_val,
                    confidence=conf_val,
                    timestamp=context.timestamp,
                    frame_id=context.frame_id,
                    metadata={"signal_id": signal_id}
                )
                
                traffic_signal_stats[signal_id] = det_res.to_dict()

                # Update local results counts
                if status_val == "Red":
                    results["red_count"] += 1
                elif status_val == "Yellow":
                    results["yellow_count"] += 1
                elif status_val == "Green":
                    results["green_count"] += 1
                elif status_val == "Unknown":
                    results["unknown_count"] += 1

                # 4. Draw overlays
                if context.working_frame is not None:
                    self._draw_overlay(context.working_frame, det["xyxy"], signal_id, status_val, conf_val)

            context.metadata["traffic_signal_detection"] = traffic_signal_stats

            # Sync totals with context metrics counters
            context.detection_counts["traffic_red"] = results["red_count"]
            context.detection_counts["traffic_yellow"] = results["yellow_count"]
            context.detection_counts["traffic_green"] = results["green_count"]
            context.detection_counts["traffic_unknown"] = results["unknown_count"]

        except Exception as e:
            logger.exception(f"TrafficSignalDetectionModule execution error: {e}")
            errors.append({"module": "traffic_signal_detection", "message": str(e)})

        return results, errors, warnings

    def _draw_overlay(self, img: np.ndarray, xyxy: List[float], signal_id: int, status_val: str, conf: float):
        """Draw bounding boxes and status banners for detected traffic signals."""
        x1, y1, x2, y2 = map(int, xyxy)
        
        # BGR Colors
        colors = {
            "Red": (68, 68, 239),
            "Yellow": (0, 215, 255),
            "Green": (129, 185, 16),
            "Unknown": (150, 150, 150)
        }
        
        color = colors.get(status_val, colors["Unknown"])
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Draw filled overlay text banner above
        label_text = f"Signal #{signal_id}: {status_val.upper()} {conf:.0%}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.35
        thickness = 1
        
        (w, h), _ = cv2.getTextSize(label_text, font, font_scale, thickness)
        
        tx = x1
        ty = max(h + 6, y1 - 4)
        
        cv2.rectangle(img, (tx, ty - h - 4), (tx + w + 4, ty + 2), color, -1)
        cv2.putText(img, label_text, (tx + 2, ty - 2), font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)

    def shutdown(self) -> None:
        self._initialized = False
        self.model = None
        logger.info("TrafficSignalDetectionModule shut down.")

    def health(self) -> bool:
        return self._initialized and self.model is not None

    def status(self) -> Dict[str, Any]:
        return {
            "name": "TrafficSignalDetectionModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "weights_path": self.weights_path,
            "active_size": self.active_size
        }
