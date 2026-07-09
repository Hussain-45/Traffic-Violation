"""
Number Plate Detection AI Module (ANPR Stage 1)
==============================================
Runs YOLOv8 number plate detection on frames, crops detected plates,
and maps ownership using PlateAssociationService.
"""
import os
import cv2
import yaml
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from loguru import logger
from ultralytics import YOLO

from ai.pipelines.base_module import BaseAIModule
from ai.pipelines.pipeline_context import PipelineContext
from ai.services.plate_association_service import plate_association_service
from ai.services.trajectory_service import trajectory_service
from shared.schemas import DetectionResult


class NumberPlateDetectionModule(BaseAIModule):
    """
    YOLOv8 number plate detector that integrates with PlateAssociationService.
    """

    def __init__(self, models_config_path: str = "configs/models.yaml", pipeline_config_path: str = "configs/pipeline.yaml"):
        self.models_config_path = models_config_path
        self.pipeline_config_path = pipeline_config_path
        self.model: Optional[YOLO] = None
        self.weights_path: Optional[str] = None
        self.active_size: str = "n"
        self.config: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Loads weights configurations and initializes YOLOv8 model."""
        if self._initialized:
            return

        # 1. Resolve weights path from models.yaml
        if os.path.exists(self.models_config_path):
            try:
                with open(self.models_config_path, "r") as f:
                    cfg = yaml.safe_load(f) or {}
                np_cfg = cfg.get("number_plate", {})
                self.active_size = np_cfg.get("active_size", "n")
                self.weights_path = np_cfg.get("sizes", {}).get(self.active_size, {}).get("weights")
                logger.info(f"Number plate model size: '{self.active_size}' with weights '{self.weights_path}'")
            except Exception as e:
                logger.error(f"Failed to load weights from {self.models_config_path}: {e}")
                self.weights_path = "models/trained/number_plate_best.pt"
        else:
            self.weights_path = "models/trained/number_plate_best.pt"

        # 2. Check weights existence and load YOLO
        if not self.weights_path or not os.path.exists(self.weights_path):
            logger.warning(f"Number plate weights file '{self.weights_path}' not found. Module running in Mock/Graceful mode.")
            self.model = None
        else:
            try:
                self.model = YOLO(self.weights_path)
                logger.info("Number Plate Detection module loaded YOLO model weights successfully.")
            except Exception as e:
                logger.exception(f"Failed to load YOLO model: {e}")
                self.model = None

        # 3. Load pipeline configs
        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                self.config = full_cfg.get("modules", {}).get("number_plate_detection", {})
            except Exception as e:
                logger.error(f"Failed to load configs from {self.pipeline_config_path}: {e}")
                self.config = {}

        self._initialized = True
        logger.info("Number Plate Detection module initialized.")

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Runs plate detection YOLO, crops plate bounding boxes,
        calls PlateAssociationService to map ownership, and outputs DetectionResult schemas.
        """
        errors = []
        warnings = []
        results = {
            "detecting_count": 0,
            "stable_count": 0,
            "unknown_count": 0,
            "crop_ready_count": 0,
            "status": "Inactive"
        }

        if not self._initialized:
            warnings.append({"module": "number_plate_detection", "message": "Module not initialized."})
            return results, errors, warnings

        # Return active status even if model is mock/missing
        results["status"] = "Active"

        if context.tracked_detections is None or len(context.tracked_detections) == 0:
            return results, errors, warnings

        try:
            min_plate_conf = self.config.get("minimum_plate_confidence", 0.50)
            min_w = self.config.get("minimum_crop_width", 30)
            min_h = self.config.get("minimum_crop_height", 10)

            plates: List[Dict[str, Any]] = []

            # 1. Run YOLO inference if model loaded
            if self.model is not None:
                model_results = self.model(frame, verbose=False)
                if model_results:
                    boxes = model_results[0].boxes
                    for box in boxes:
                        conf = float(box.conf[0].item())
                        if conf < min_plate_conf:
                            continue
                        
                        xyxy = box.xyxy[0].tolist()
                        px1, py1, px2, py2 = map(int, xyxy)
                        pw = px2 - px1
                        ph = py2 - py1

                        # Validate crop dimensions
                        if pw >= min_w and ph >= min_h:
                            # Safe crop boundary checks
                            img_h, img_w = frame.shape[:2]
                            cx1 = max(0, px1)
                            cy1 = max(0, py1)
                            cx2 = min(img_w, px2)
                            cy2 = min(img_h, py2)

                            cropped = frame[cy1:cy2, cx1:cx2].copy()
                            plates.append({
                                "id": None,
                                "bbox": xyxy,
                                "conf": conf,
                                "cropped_image": cropped
                            })

            # 2. Filter vehicle candidates from tracking detections
            # COCO classes: 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
            vehicles = []
            tracked = context.tracked_detections
            if tracked.xyxy is not None and tracked.tracker_id is not None:
                for idx in range(len(tracked)):
                    cls_idx = int(tracked.class_id[idx])
                    if cls_idx in (2, 3, 5, 7):
                        v_box = tracked.xyxy[idx].tolist()
                        v_id = int(tracked.tracker_id[idx])
                        v_conf = float(tracked.confidence[idx])
                        vehicles.append({
                            "id": v_id,
                            "bbox": v_box,
                            "class_id": cls_idx,
                            "conf": v_conf
                        })

            # 3. Associate plates to vehicles
            plate_association_service.associate_all(vehicles, plates, context.timestamp, context.frame_id)

            # 4. Map results to DetectionResults and metadata payload
            plate_stats = {}
            for vehicle in vehicles:
                v_id = vehicle["id"]
                v_box = vehicle["bbox"]
                v_class = vehicle["class_id"]

                assoc = plate_association_service.get_association(v_id)
                if assoc is not None:
                    status_val = "Unknown"
                    if assoc.stable_plate is not None:
                        status_val = "Stable Plate"
                        results["stable_count"] += 1
                    elif assoc.associated_plate is not None:
                        status_val = "Detecting"
                        results["detecting_count"] += 1
                    else:
                        results["unknown_count"] += 1

                    is_crop_ready = (assoc.associated_plate is not None and 
                                     assoc.associated_plate.cropped_plate_image is not None)
                    if is_crop_ready:
                        results["crop_ready_count"] += 1

                    # Extract plate bbox for overlays/metadata
                    plate_bbox = assoc.associated_plate.plate_bbox if assoc.associated_plate else None
                    stable_dict = assoc.stable_plate.to_dict() if assoc.stable_plate else None

                    det_res = DetectionResult(
                        module_name="number_plate_detection",
                        tracking_id=v_id,
                        vehicle_class=int(v_class),
                        status=status_val,
                        confidence=assoc.association_confidence,
                        timestamp=context.timestamp,
                        frame_id=context.frame_id,
                        region=v_box,
                        metadata={
                            "plate_bbox": plate_bbox,
                            "association_confidence": assoc.association_confidence,
                            "plate_visibility": 1.0 if assoc.associated_plate else 0.0,
                            "plate_crop_ready": is_crop_ready,
                            "stable_plate": stable_dict
                        }
                    )
                    plate_stats[v_id] = det_res.to_dict()

                    # 5. Draw overlays
                    if context.working_frame is not None:
                        self._draw_overlay(context.working_frame, v_box, v_id, status_val, plate_bbox)

            context.metadata["number_plate_detection"] = plate_stats

            # Sync counts
            context.detection_counts["anpr_detecting"] = results["detecting_count"]
            context.detection_counts["anpr_stable"] = results["stable_count"]
            context.detection_counts["anpr_unknown"] = results["unknown_count"]
            context.detection_counts["anpr_crops"] = results["crop_ready_count"]

        except Exception as e:
            logger.exception(f"NumberPlateDetectionModule process error: {e}")
            errors.append({"module": "number_plate_detection", "message": str(e)})

        return results, errors, warnings

    def _draw_overlay(self, img: np.ndarray, vehicle_box: List[float], v_id: int, status_val: str, plate_box: Optional[List[float]]) -> None:
        """Draw bounding boxes and status labels."""
        # 1. Draw vehicle box card
        vx1, vy1, vx2, vy2 = map(int, vehicle_box)
        
        # Colors (BGR)
        colors = {
            "Stable Plate": (129, 185, 16),   # Green
            "Detecting": (16, 185, 245),      # Yellow
            "Unknown": (150, 150, 150)        # Gray
        }

        color = colors.get(status_val, colors["Unknown"])
        
        # 2. Draw plate box if available
        if plate_box:
            px1, py1, px2, py2 = map(int, plate_box)
            cv2.rectangle(img, (px1, py1), (px2, py2), color, 2)
            
            # Optional association line
            pcx = (px1 + px2) // 2
            pcy = (py1 + py2) // 2
            vcx = (vx1 + vx2) // 2
            vcy = (vy1 + vy2) // 2
            cv2.line(img, (pcx, pcy), (vcx, vcy), color, 1, lineType=cv2.LINE_AA)

        # 3. Label details banner
        label_text = f"Vehicle #{v_id}: "
        if status_val == "Stable Plate":
            label_text += "ANPR STABLE"
        elif status_val == "Detecting":
            label_text += "ANPR DETECTING"
        else:
            label_text += "ANPR UNKNOWN"

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.35
        thickness = 1

        (w, h), _ = cv2.getTextSize(label_text, font, font_scale, thickness)
        tx = vx1
        ty = max(h + 6, vy1 - 4)

        cv2.rectangle(img, (tx, ty - h - 4), (tx + w + 4, ty + 2), color, -1)
        cv2.putText(img, label_text, (tx + 2, ty - 2), font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)

    def shutdown(self) -> None:
        self._initialized = False
        logger.info("Number Plate Detection module shut down.")

    def health(self) -> bool:
        return self._initialized

    def status(self) -> Dict[str, Any]:
        return {
            "name": "NumberPlateDetectionModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "config": self.config
        }
