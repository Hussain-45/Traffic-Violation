"""
Seat Belt Detection AI Module
=============================
Executes YOLOv8 seat belt and occupant indicator detection, splits vehicle 
windshield regions into Driver (Right) and Passenger (Left) halves, 
associates seat belt status, and draws annotated overlays.
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


class SeatBeltDetectionModule(BaseAIModule):
    """
    YOLOv8-based Seat Belt Detection Module that integrates into the AI Pipeline.
    Only evaluates eligible tracked vehicles (car, truck, bus).
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
                sb_cfg = cfg.get("seat_belt", {})
                self.active_size = sb_cfg.get("active_size", "n")
                sizes = sb_cfg.get("sizes", {})
                self.weights_path = sizes.get(self.active_size, {}).get("weights")
                logger.info(f"Seat Belt model size configured: '{self.active_size}' with weights '{self.weights_path}'")
            except Exception as e:
                logger.error(f"Error parsing {self.models_config_path}: {e}. Using default weights.")
                self.weights_path = "models/trained/seatbelt_best.pt"
        else:
            logger.warning(f"{self.models_config_path} not found. Using default weights path.")
            self.weights_path = "models/trained/seatbelt_best.pt"

        # 2. Check weights existence and load model
        if not self.weights_path or not os.path.exists(self.weights_path):
            logger.warning(f"Seat Belt weights not found at '{self.weights_path}'. Seat Belt detection will run in Mock/Disabled mode.")
            self.model = None
        else:
            try:
                logger.info(f"Loading Seat Belt Detection model from '{self.weights_path}'...")
                self.model = YOLO(self.weights_path)
                logger.info("Seat Belt Detection model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Seat Belt model: {e}")
                self.model = None

        self._initialized = True

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processes the frame, matches seat belt detections to driver/passenger regions
        of tracked vehicles, and annotates overlays on working_frame.
        """
        errors = []
        warnings = []
        results = {
            "seat_belt_count": 0,
            "no_seat_belt_count": 0,
            "unknown_count": 0,
            "violators": [],
            "status": "Inactive"
        }

        # 1. Check if model is loaded
        if self.model is None:
            msg = "Seat Belt model not trained / weights missing"
            context.add_warning("seat_belt_detection", msg)
            warnings.append({"module": "seat_belt_detection", "message": msg})
            return results, errors, warnings

        if context.tracked_detections is None or len(context.tracked_detections) == 0:
            results["status"] = "Active"
            return results, errors, warnings

        results["status"] = "Active"

        try:
            # Get confidence threshold from pipeline context config or use default
            conf_threshold = context.config.get("seat_belt_detection", {}).get("confidence_threshold", 0.50)

            # 2. Run model on full frame
            # Classes: 0 = yawn, 1 = eyesclosed, 2 = seatbelt, 3 = mobile, 4 = cigarette
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

            # 3. Filter tracked detections for eligible vehicles
            # COCO classes: 2 = car, 5 = bus, 7 = truck
            eligible_vehicles = []
            for i in range(len(context.tracked_detections)):
                cls_idx = int(context.tracked_detections.class_id[i])
                if cls_idx in [2, 5, 7]:  # car, bus, truck
                    x1, y1, x2, y2 = context.tracked_detections.xyxy[i]
                    track_id = int(context.tracked_detections.tracker_id[i]) if context.tracked_detections.tracker_id is not None else None
                    conf = float(context.tracked_detections.confidence[i])
                    eligible_vehicles.append({
                        "xyxy": [x1, y1, x2, y2],
                        "track_id": track_id,
                        "class_id": cls_idx,
                        "conf": conf
                    })

            seat_belt_stats = {}

            # 4. wind-shield subdivision and occupant evaluation
            for vehicle in eligible_vehicles:
                # Use shared DriverRegionService to resolve occupant regions
                regions = DriverRegionService.get_occupant_regions(vehicle["xyxy"], windshield_height_ratio=0.50, drive_side="RHD")
                driver_box = regions["driver"]
                passenger_box = regions["passenger"]


                # Evaluate occupants
                driver_status, driver_conf = self._evaluate_region(driver_box, model_dets)
                passenger_status, passenger_conf = self._evaluate_region(passenger_box, model_dets)

                # Track IDs state binding
                track_id = vehicle["track_id"]
                seat_belt_stats[track_id] = {
                    "driver": {"status": driver_status, "confidence": driver_conf},
                    "passenger": {"status": passenger_status, "confidence": passenger_conf}
                }

                # Update global metrics counts
                for status_val in [driver_status, passenger_status]:
                    if status_val == "Seat Belt":
                        results["seat_belt_count"] += 1
                    elif status_val == "No Seat Belt":
                        results["no_seat_belt_count"] += 1
                    elif status_val == "Unknown":
                        results["unknown_count"] += 1

                # If driver or passenger is a violator, log it
                if driver_status == "No Seat Belt" or passenger_status == "No Seat Belt":
                    results["violators"].append({
                        "vehicle_id": track_id,
                        "driver_violator": (driver_status == "No Seat Belt"),
                        "passenger_violator": (passenger_status == "No Seat Belt")
                    })

                # 5. Draw visualization overlays
                if context.working_frame is not None:
                    self._draw_overlay(
                        context.working_frame, 
                        vehicle["xyxy"], 
                        track_id, 
                        driver_status, 
                        driver_conf, 
                        passenger_status, 
                        passenger_conf
                    )

            context.metadata["seat_belt_detection"] = seat_belt_stats

            # Sync totals with context metrics counters
            context.detection_counts["seat_belt"] = results["seat_belt_count"]
            context.detection_counts["no_seat_belt"] = results["no_seat_belt_count"]
            context.detection_counts["unknown_seat_belt"] = results["unknown_count"]

        except Exception as e:
            logger.exception(f"SeatBeltDetectionModule execution error: {e}")
            errors.append({"module": "seat_belt_detection", "message": str(e)})

        return results, errors, warnings

    def _evaluate_region(self, region_box: List[float], model_dets: List[Dict[str, Any]]) -> Tuple[str, float]:
        """Evaluates whether an occupant is wearing a seat belt in the designated windshield region."""
        rx1, ry1, rx2, ry2 = region_box
        
        region_dets = []
        has_seatbelt = False
        seatbelt_conf = 0.0
        
        # Check detections falling inside the region
        for det in model_dets:
            dcx, dcy = det["center"]
            if rx1 <= dcx <= rx2 and ry1 <= dcy <= ry2:
                region_dets.append(det)
                if det["cls"] == 2:  # seatbelt
                    has_seatbelt = True
                    seatbelt_conf = max(seatbelt_conf, det["conf"])

        if len(region_dets) == 0:
            # No occupant indicators detected in this region
            return "Unknown", 0.0

        if has_seatbelt:
            return "Seat Belt", seatbelt_conf
        else:
            # Occupants detected (yawn, eyesclosed, mobile, cigarette) but no seatbelt found
            max_conf = max(d["conf"] for d in region_dets)
            return "No Seat Belt", max_conf

    def _draw_overlay(
        self, img: np.ndarray, vehicle_xyxy: List[float], track_id: Optional[int], 
        driver_status: str, driver_conf: float, passenger_status: str, passenger_conf: float
    ):
        """Draw a text banner displaying driver/passenger seat belt details on top of the vehicle."""
        vx1, vy1, vx2, vy2 = map(int, vehicle_xyxy)
        
        # Set colors
        # Green for Seat Belt, Red for No Seat Belt, Gray for Unknown
        colors = {
            "Seat Belt": (129, 185, 16),
            "No Seat Belt": (68, 68, 239),
            "Unknown": (150, 150, 150)
        }
        
        d_color = colors[driver_status]
        p_color = colors[passenger_status]
        
        # Label lines
        vehicle_label = f"Vehicle #{track_id}" if track_id is not None else "Vehicle"
        driver_label = f"Driver: {driver_status}" + (f" {driver_conf:.0%}" if driver_conf > 0 else "")
        passenger_label = f"Passenger: {passenger_status}" + (f" {passenger_conf:.0%}" if passenger_conf > 0 else "")

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.35
        thickness = 1
        
        (w1, h1), _ = cv2.getTextSize(vehicle_label, font, font_scale, thickness)
        (w2, h2), _ = cv2.getTextSize(driver_label, font, font_scale, thickness)
        (w3, h3), _ = cv2.getTextSize(passenger_label, font, font_scale, thickness)
        
        banner_w = max(w1, w2, w3) + 12
        banner_h = h1 + h2 + h3 + 18
        
        bx1 = vx1
        by1 = max(0, vy1 - banner_h)
        bx2 = vx1 + banner_w
        by2 = vy1
        
        # Draw background container box
        cv2.rectangle(img, (bx1, by1), (bx2, by2), (30, 30, 30), -1)
        # Draw borders indicating severity (red if any violation exists, green if both buckled, else gray)
        border_color = (68, 68, 239) if (driver_status == "No Seat Belt" or passenger_status == "No Seat Belt") \
                       else (129, 185, 16) if (driver_status == "Seat Belt" and passenger_status == "Seat Belt") \
                       else (150, 150, 150)
        cv2.rectangle(img, (bx1, by1), (bx2, by2), border_color, 1)
        
        # Draw text lines
        cv2.putText(img, vehicle_label, (bx1 + 6, by1 + h1 + 4), font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)
        cv2.putText(img, driver_label, (bx1 + 6, by1 + h1 + h2 + 9), font, font_scale, d_color, thickness, lineType=cv2.LINE_AA)
        cv2.putText(img, passenger_label, (bx1 + 6, by1 + h1 + h2 + h3 + 14), font, font_scale, p_color, thickness, lineType=cv2.LINE_AA)

    def shutdown(self) -> None:
        self._initialized = False
        self.model = None
        logger.info("SeatBeltDetectionModule shut down.")

    def health(self) -> bool:
        return self._initialized and self.model is not None

    def status(self) -> Dict[str, Any]:
        return {
            "name": "SeatBeltDetectionModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "weights_path": self.weights_path,
            "active_size": self.active_size
        }
