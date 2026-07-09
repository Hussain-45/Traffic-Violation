"""
Helmet Detection AI Module
===========================
Executes YOLOv8 helmet detection, filters the results to motorcycle riders,
spatially associates helmet/no-helmet classes with vehicle tracking IDs,
and draws annotated overlays.
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



class HelmetDetectionModule(BaseAIModule):
    """
    YOLOv8-based Helmet Detection Module that integrates into the AI Pipeline.
    Only evaluates tracked motorcycles and persons riding them.
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
                helmet_cfg = cfg.get("helmet", {})
                self.active_size = helmet_cfg.get("active_size", "n")
                sizes = helmet_cfg.get("sizes", {})
                self.weights_path = sizes.get(self.active_size, {}).get("weights")
                logger.info(f"Helmet model size configured: '{self.active_size}' with weights '{self.weights_path}'")
            except Exception as e:
                logger.error(f"Error parsing {self.models_config_path}: {e}. Using default weights.")
                self.weights_path = "models/trained/helmet_best.pt"
        else:
            logger.warning(f"{self.models_config_path} not found. Using default weights path.")
            self.weights_path = "models/trained/helmet_best.pt"

        # 2. Check weights existence and load model
        if not self.weights_path or not os.path.exists(self.weights_path):
            logger.warning(f"Helmet weights not found at '{self.weights_path}'. Helmet detection will run in Mock/Disabled mode.")
            self.model = None
        else:
            try:
                logger.info(f"Loading Helmet Detection model from '{self.weights_path}'...")
                self.model = YOLO(self.weights_path)
                logger.info("Helmet Detection model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Helmet model: {e}")
                self.model = None

        self._initialized = True

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processes the frame, matches helmet detections to motorcyclist tracks,
        and annotates overlays on working_frame.
        """
        errors = []
        warnings = []
        results = {
            "helmet_count": 0,
            "no_helmet_count": 0,
            "violators": [],
            "status": "Inactive"
        }

        # 1. Check if model is trained and loaded
        if self.model is None:
            msg = "Helmet model not trained / weights missing"
            context.add_warning("helmet_detection", msg)
            warnings.append({"module": "helmet_detection", "message": msg})
            return results, errors, warnings

        if context.tracked_detections is None or len(context.tracked_detections) == 0:
            # No vehicles tracked in this frame, skip
            results["status"] = "Active"
            return results, errors, warnings

        results["status"] = "Active"

        try:
            # 2. Run helmet detection model on the full frame
            # YOLO classes: 0 = helmet, 1 = no_helmet
            model_results = self.model(frame, verbose=False)
            if not model_results:
                return results, errors, warnings

            helmet_detections = model_results[0].boxes
            
            # Group helmet detections
            helmets: List[Dict[str, Any]] = []
            for box in helmet_detections:
                cls_idx = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()
                helmets.append({
                    "cls": cls_idx,  # 0 = helmet, 1 = no_helmet
                    "conf": conf,
                    "xyxy": xyxy,
                    "center": ((xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2)
                })

            # 3. Identify motorcycles and rider persons from tracked_detections
            # COCO classes: 0 = person, 3 = motorcycle
            motorcycles = []
            persons = []

            for i in range(len(context.tracked_detections)):
                x1, y1, x2, y2 = context.tracked_detections.xyxy[i]
                cls_idx = int(context.tracked_detections.class_id[i])
                track_id = int(context.tracked_detections.tracker_id[i]) if context.tracked_detections.tracker_id is not None else None
                conf = float(context.tracked_detections.confidence[i])

                det_obj = {"xyxy": [x1, y1, x2, y2], "track_id": track_id, "conf": conf}
                if cls_idx == 3:  # motorcycle
                    motorcycles.append(det_obj)
                elif cls_idx == 0:  # person
                    persons.append(det_obj)

            # 4. Associate persons riding motorcycles
            # If a person box overlaps significantly with a motorcycle box, they are a rider.
            riders: List[Dict[str, Any]] = []
            for p in persons:
                px1, py1, px2, py2 = p["xyxy"]
                p_area = (px2 - px1) * (py2 - py1)
                if p_area <= 0:
                    continue

                for m in motorcycles:
                    mx1, my1, mx2, my2 = m["xyxy"]
                    # Calculate intersection box
                    ix1 = max(px1, mx1)
                    iy1 = max(py1, my1)
                    ix2 = min(px2, mx2)
                    iy2 = min(py2, my2)

                    if ix2 > ix1 and iy2 > iy1:
                        i_area = (ix2 - ix1) * (iy2 - iy1)
                        # If overlap is > 10% of person's area, classify as rider
                        if i_area / p_area > 0.10:
                            riders.append({
                                "xyxy": p["xyxy"],
                                "track_id": m["track_id"],  # Associate to motorcycle ID
                                "rider_track_id": p["track_id"]
                            })
                            break

            # If no persons are explicitly associated but we have tracked motorcycles,
            # use the motorcycle boxes as fallback rider regions (checking top 50% of the box)
            motorcycles_without_riders = [
                m for m in motorcycles 
                if not any(r["track_id"] == m["track_id"] for r in riders)
            ]
            for m in motorcycles_without_riders:
                fallback_box = DriverRegionService.get_motorcycle_rider_fallback(m["xyxy"], height_ratio=0.50)
                riders.append({
                    "xyxy": fallback_box,
                    "track_id": m["track_id"],
                    "rider_track_id": None
                })

            # 5. Spatial Containment matching
            # For each rider, find if a helmet or no_helmet box falls inside or overlaps heavily
            helmet_stats = {}
            for r in riders:
                rx1, ry1, rx2, ry2 = r["xyxy"]
                
                # Restrict search area to upper portion of the rider box (head region) using DriverRegionService
                head_box = DriverRegionService.get_rider_head_region(r["xyxy"], head_height_ratio=0.45)
                head_y2 = head_box[3]

                best_match = None
                max_overlap_ratio = 0.0

                for h in helmets:
                    hx1, hy1, hx2, hy2 = h["xyxy"]
                    hcx, hcy = h["center"]

                    # Quick containment check: Is helmet center inside the upper portion of the rider box?
                    # Or does it intersect the rider's box?
                    if rx1 <= hcx <= rx2 and ry1 <= hcy <= head_y2:
                        # Calculate overlap ratio of helmet area
                        h_w = hx2 - hx1
                        h_h = hy2 - hy1
                        h_area = h_w * h_h
                        if h_area <= 0:
                            continue
                        
                        ix1 = max(rx1, hx1)
                        iy1 = max(ry1, hy1)
                        ix2 = min(rx2, hx2)
                        iy2 = min(head_y2, hy2)
                        
                        overlap_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                        overlap_ratio = overlap_area / h_area
                        
                        if overlap_ratio > max_overlap_ratio:
                            max_overlap_ratio = overlap_ratio
                            best_match = h

                # If found a match, associate state
                if best_match is not None:
                    track_id = r["track_id"]
                    is_helmet = (best_match["cls"] == 0)
                    conf = best_match["conf"]
                    
                    helmet_stats[track_id] = {
                        "helmet": is_helmet,
                        "confidence": conf,
                        "bbox": best_match["xyxy"]
                    }
                    
                    if is_helmet:
                        results["helmet_count"] += 1
                    else:
                        results["no_helmet_count"] += 1
                        results["violators"].append({
                            "motorcycle_id": track_id,
                            "confidence": conf
                        })
                    
                    # 6. Render overlays on context.working_frame
                    if context.working_frame is not None:
                        self._draw_overlay(context.working_frame, r["xyxy"], track_id, is_helmet, conf)

            # Store in context metadata
            context.metadata["helmet_detection"] = helmet_stats
            
            # Update counts directly in context detection counts for API compatibility
            context.detection_counts["helmet"] = results["helmet_count"]
            context.detection_counts["no_helmet"] = results["no_helmet_count"]

        except Exception as e:
            logger.exception(f"HelmetDetectionModule execution error: {e}")
            errors.append({"module": "helmet_detection", "message": str(e)})

        return results, errors, warnings

    def _draw_overlay(self, img: np.ndarray, rider_xyxy: List[float], track_id: Optional[int], is_helmet: bool, conf: float):
        """Draw distinct Helmet / No Helmet overlay boxes and text banners on the frame."""
        rx1, ry1, rx2, ry2 = map(int, rider_xyxy)
        
        # Color mapping (BGR)
        # Emerald Green for Helmet, Rose Red for No Helmet
        color = (129, 185, 16) if is_helmet else (68, 68, 239)
        status_text = "Helmet" if is_helmet else "No Helmet"
        status_icon = "OK" if is_helmet else "ALERT"
        
        # Draw bounding border around head region using DriverRegionService
        head_box = DriverRegionService.get_rider_head_region(rider_xyxy, head_height_ratio=0.35)
        hx1, hy1, hx2, hy2 = map(int, head_box)
        cv2.rectangle(img, (hx1, hy1), (hx2, hy2), color, 2)
        
        # Label text
        motorcycle_label = f"Motorcycle #{track_id}" if track_id is not None else "Motorcycle"
        helmet_label = f"{status_text} {conf:.0%}"
        
        # Draw text background banner
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.40
        thickness = 1
        
        (w1, h1), _ = cv2.getTextSize(motorcycle_label, font, font_scale, thickness)
        (w2, h2), _ = cv2.getTextSize(helmet_label, font, font_scale, thickness)
        
        banner_w = max(w1, w2) + 10
        banner_h = h1 + h2 + 12
        
        bx1 = rx1
        by1 = max(0, ry1 - banner_h)
        bx2 = rx1 + banner_w
        by2 = ry1
        
        # Draw filled overlay banner
        cv2.rectangle(img, (bx1, by1), (bx2, by2), color, -1)
        
        # Draw text lines inside banner
        cv2.putText(img, motorcycle_label, (bx1 + 5, by1 + h1 + 3), font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)
        cv2.putText(img, helmet_label, (bx1 + 5, by1 + h1 + h2 + 8), font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)

    def shutdown(self) -> None:
        self._initialized = False
        self.model = None
        logger.info("HelmetDetectionModule shut down.")

    def health(self) -> bool:
        # Healthy if initialized, and if weights path exists (meaning it can run inference)
        return self._initialized and self.model is not None

    def status(self) -> Dict[str, Any]:
        return {
            "name": "HelmetDetectionModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "weights_path": self.weights_path,
            "active_size": self.active_size
        }
