"""
Mobile Phone Detection AI Module
================================
Executes YOLOv8 driver mobile phone detection, uses central DriverRegionService 
to target the driver zone, evaluates phone usage states, and draws annotated overlays.
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
from ai.services.driver_region_service import DriverRegionService
from shared.schemas import DetectionResult



class MobilePhoneDetectionModule(BaseAIModule):
    """
    YOLOv8-based Mobile Phone Detection Module.
    Only evaluates the driver region of eligible tracked vehicles (car, truck, bus).
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
                mp_cfg = cfg.get("mobile_phone", {})
                self.active_size = mp_cfg.get("active_size", "n")
                sizes = mp_cfg.get("sizes", {})
                self.weights_path = sizes.get(self.active_size, {}).get("weights")
                logger.info(f"Mobile Phone model size configured: '{self.active_size}' with weights '{self.weights_path}'")
            except Exception as e:
                logger.error(f"Error parsing {self.models_config_path}: {e}. Using default weights.")
                self.weights_path = "models/trained/mobile_best.pt"
        else:
            logger.warning(f"{self.models_config_path} not found. Using default weights path.")
            self.weights_path = "models/trained/mobile_best.pt"

        # 2. Check weights existence and load model
        if not self.weights_path or not os.path.exists(self.weights_path):
            logger.warning(f"Mobile Phone weights not found at '{self.weights_path}'. Mobile Phone detection will run in Mock/Disabled mode.")
            self.model = None
        else:
            try:
                logger.info(f"Loading Mobile Phone Detection model from '{self.weights_path}'...")
                self.model = YOLO(self.weights_path)
                logger.info("Mobile Phone Detection model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Mobile Phone model: {e}")
                self.model = None

        self._initialized = True

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processes the frame, matches mobile phone detections to driver regions,
        and annotates overlays on working_frame.
        """
        errors = []
        warnings = []
        results = {
            "phone_count": 0,
            "no_phone_count": 0,
            "unknown_count": 0,
            "violators": [],
            "status": "Inactive"
        }

        # 1. Check if model is loaded
        if self.model is None:
            msg = "Mobile Phone model not trained / weights missing"
            context.add_warning("mobile_phone_detection", msg)
            warnings.append({"module": "mobile_phone_detection", "message": msg})
            return results, errors, warnings

        if context.tracked_detections is None or len(context.tracked_detections) == 0:
            results["status"] = "Active"
            return results, errors, warnings

        results["status"] = "Active"

        try:
            # Get confidence threshold from pipeline context config
            conf_threshold = context.config.get("mobile_phone_detection", {}).get("confidence_threshold", 0.50)

            # 2. Run model on full frame
            # Classes: 0 = cigarette, 1 = phone, 2 = seatbelt
            model_results = self.model(frame, verbose=False)
            if not model_results:
                return results, errors, warnings

            detections = model_results[0].boxes
            
            # Group model detections
            model_dets: List[Dict[str, Any]] = []
            for box in detections:
                cls_idx = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                if conf < conf_threshold:
                    continue
                xyxy = box.xyxy[0].tolist()
                model_dets.append({
                    "cls": cls_idx,
                    "conf": conf,
                    "xyxy": xyxy,
                    "center": ((xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2)
                })

            # 3. Filter tracked detections for eligible vehicles (car=2, bus=5, truck=7)
            eligible_vehicles = []
            for i in range(len(context.tracked_detections)):
                cls_idx = int(context.tracked_detections.class_id[i])
                if cls_idx in [2, 5, 7]:
                    x1, y1, x2, y2 = context.tracked_detections.xyxy[i]
                    track_id = int(context.tracked_detections.tracker_id[i]) if context.tracked_detections.tracker_id is not None else None
                    conf = float(context.tracked_detections.confidence[i])
                    eligible_vehicles.append({
                        "xyxy": [x1, y1, x2, y2],
                        "track_id": track_id,
                        "class_id": cls_idx,
                        "conf": conf
                    })

            mobile_phone_stats = {}

            # 4. Driver region evaluation using DriverRegionService
            for vehicle in eligible_vehicles:
                # Windshield & Driver subdivision (RHD)
                regions = DriverRegionService.get_occupant_regions(vehicle["xyxy"], windshield_height_ratio=0.50, drive_side="RHD")
                driver_box = regions["driver"]
                
                # Check for mobile phone and occupants
                status_val, conf_val = self._evaluate_driver(driver_box, model_dets)
                
                track_id = vehicle["track_id"]
                det_res = DetectionResult(
                    module_name="mobile_phone_detection",
                    tracking_id=track_id,
                    vehicle_class=vehicle["class_id"],
                    region=driver_box,
                    status=status_val,
                    confidence=conf_val,
                    timestamp=context.timestamp,
                    frame_id=context.frame_id,
                    metadata={}  # Module-specific metadata only
                )
                mobile_phone_stats[track_id] = det_res.to_dict()

                # Update count metrics
                if status_val == "Mobile Phone":
                    results["phone_count"] += 1
                    results["violators"].append({
                        "vehicle_id": track_id,
                        "confidence": conf_val
                    })
                elif status_val == "No Mobile Phone":
                    results["no_phone_count"] += 1
                elif status_val == "Unknown":
                    results["unknown_count"] += 1

                # 5. Draw overlays
                if context.working_frame is not None:
                    self._draw_overlay(context.working_frame, vehicle["xyxy"], track_id, status_val, conf_val)

            context.metadata["mobile_phone_detection"] = mobile_phone_stats

            # Sync totals with context metrics counters
            context.detection_counts["mobile_phone"] = results["phone_count"]
            context.detection_counts["no_mobile_phone"] = results["no_phone_count"]
            context.detection_counts["unknown_mobile_phone"] = results["unknown_count"]

        except Exception as e:
            logger.exception(f"MobilePhoneDetectionModule execution error: {e}")
            errors.append({"module": "mobile_phone_detection", "message": str(e)})

        return results, errors, warnings

    def _evaluate_driver(self, driver_box: List[float], model_dets: List[Dict[str, Any]]) -> Tuple[str, float]:
        """Evaluates whether the driver is using a phone in the designated windshield region."""
        dx1, dy1, dx2, dy2 = driver_box
        
        driver_dets = []
        has_phone = False
        phone_conf = 0.0
        
        for det in model_dets:
            dcx, dcy = det["center"]
            if dx1 <= dcx <= dx2 and dy1 <= dcy <= dy2:
                driver_dets.append(det)
                if det["cls"] == 1:  # phone
                    has_phone = True
                    phone_conf = max(phone_conf, det["conf"])

        if len(driver_dets) == 0:
            return "Unknown", 0.0

        if has_phone:
            return "Mobile Phone", phone_conf
        else:
            # Detections found in driver region (cigarette, seatbelt) but no phone, meaning driver is present
            max_conf = max(d["conf"] for d in driver_dets)
            return "No Mobile Phone", max_conf

    def _draw_overlay(self, img: np.ndarray, vehicle_xyxy: List[float], track_id: Optional[int], status_val: str, conf: float):
        """Draw driver phone status overlay labels on the vehicle's bounding box."""
        vx1, vy1, vx2, vy2 = map(int, vehicle_xyxy)
        
        # Color codes (BGR)
        # Green for No Phone, Red for Phone, Gray for Unknown
        colors = {
            "No Mobile Phone": (129, 185, 16),
            "Mobile Phone": (68, 68, 239),
            "Unknown": (150, 150, 150)
        }
        
        color = colors[status_val]
        status_text = "Phone: "
        if status_val == "Mobile Phone":
            status_text += f"📱 {conf:.0%}"
        elif status_val == "No Mobile Phone":
            status_text += f"✅ {conf:.0%}"
        else:
            status_text += "⚪ Unknown"

        # Windshield Driver boundary coordinates
        regions = DriverRegionService.get_occupant_regions(vehicle_xyxy, windshield_height_ratio=0.50, drive_side="RHD")
        dx1, dy1, dx2, dy2 = map(int, regions["driver"])
        
        # Draw a small bounding box outline around the driver region
        cv2.rectangle(img, (dx1, dy1), (dx2, dy2), color, 1)

        # Label above driver region
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.30
        thickness = 1
        
        (w, h), _ = cv2.getTextSize(status_text, font, font_scale, thickness)
        
        # Position box above driver windshield area
        tx = dx1 + 4
        ty = dy1 + h + 4
        
        # Text background
        cv2.rectangle(img, (tx - 2, ty - h - 2), (tx + w + 2, ty + 2), (30, 30, 30), -1)
        cv2.putText(img, status_text, (tx, ty), font, font_scale, color, thickness, lineType=cv2.LINE_AA)

    def shutdown(self) -> None:
        self._initialized = False
        self.model = None
        logger.info("MobilePhoneDetectionModule shut down.")

    def health(self) -> bool:
        return self._initialized and self.model is not None

    def status(self) -> Dict[str, Any]:
        return {
            "name": "MobilePhoneDetectionModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "weights_path": self.weights_path,
            "active_size": self.active_size
        }
