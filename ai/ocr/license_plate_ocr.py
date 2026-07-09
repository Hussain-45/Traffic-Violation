"""
License Plate OCR AI Module (ANPR Stage 2)
=========================================
Runs OCR (EasyOCR by default) on stable number plate crops,
and processes character sequences using PlateRecognitionService.
"""
import os
import cv2
import yaml
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from loguru import logger

from ai.pipelines.base_module import BaseAIModule
from ai.pipelines.pipeline_context import PipelineContext
from ai.services.plate_association_service import plate_association_service
from ai.services.plate_recognition_service import plate_recognition_service
from shared.schemas import DetectionResult


class LicensePlateOCRModule(BaseAIModule):
    """
    OCR Module that wraps EasyOCR and integrates with PlateRecognitionService.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.config: Dict[str, Any] = {}
        self.reader: Optional[Any] = None
        self._initialized = False
        self.engine_name = "easyocr"

    def initialize(self) -> None:
        """Initializes the OCR engine based on pipeline configurations."""
        if self._initialized:
            return

        # 1. Load pipeline configurations
        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                self.config = full_cfg.get("modules", {}).get("ocr", {})
            except Exception as e:
                logger.error(f"Failed to load OCR configs from {self.pipeline_config_path}: {e}")
                self.config = {}

        self.engine_name = self.config.get("ocr_engine", "easyocr")
        gpu = self.config.get("gpu", False)
        lang = self.config.get("language", "en")

        # 2. Initialize primary OCR reader (EasyOCR)
        if self.engine_name == "easyocr":
            try:
                import easyocr
                # Suppress download warnings and initialize
                self.reader = easyocr.Reader([lang], gpu=gpu)
                logger.info(f"EasyOCR reader initialized (gpu={gpu}, language='{lang}').")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR reader: {e}. Running in Mock/Graceful mode.")
                self.reader = None
        else:
            logger.warning(f"OCR engine '{self.engine_name}' not supported natively. Running in Mock/Graceful mode.")
            self.reader = None

        self._initialized = True
        logger.info("License Plate OCR Module initialized.")

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], list, list]:
        """
        Retrieves stable crops from PlateAssociationService, runs OCR,
        sends result to PlateRecognitionService, and returns DetectionResults.
        """
        errors = []
        warnings = []
        results = {
            "requests_count": 0,
            "verified_count": 0,
            "rejected_count": 0,
            "avg_confidence": 0.0,
            "status": "Inactive"
        }

        if not self._initialized:
            warnings.append({"module": "ocr", "message": "Module not initialized."})
            return results, errors, warnings

        results["status"] = "Active"

        try:
            min_ocr_conf = self.config.get("minimum_ocr_confidence", 0.50)
            max_rotation = self.config.get("maximum_crop_rotation", 15.0)

            # Map: vehicle_tracking_id -> DetectionResult dict representation
            ocr_results = {}
            confidences_list = []

            # 1. Fetch active associations
            for v_id, assoc in list(plate_association_service.associations.items()):
                # Only process if a stable plate crop is available
                if assoc.stable_plate is None or assoc.stable_plate.cropped_plate_image is None:
                    continue

                crop = assoc.stable_plate.cropped_plate_image
                if crop.size == 0:
                    continue

                results["requests_count"] += 1

                # Deskew/Rotate if crop rotation is detected (optional but helpful placeholder check)
                # For basic implementation, we run OCR directly on the crop
                recognized_text = ""
                ocr_conf = 0.0

                # 2. Execute OCR Extraction
                if self.reader is not None:
                    try:
                        # EasyOCR returns list of tuples: (bbox, text, confidence)
                        ocr_outputs = self.reader.readtext(crop)
                        if ocr_outputs:
                            # Choose candidate with highest confidence
                            best_ocr = max(ocr_outputs, key=lambda x: x[2])
                            recognized_text = best_ocr[1]
                            ocr_conf = float(best_ocr[2])
                    except Exception as ocr_err:
                        logger.error(f"OCR execution failed for Vehicle #{v_id}: {ocr_err}")
                        recognized_text = ""
                        ocr_conf = 0.0

                # 3. Process result through PlateRecognitionService (normalization, validation, voting)
                rec_state = plate_recognition_service.process_ocr_result(
                    vehicle_id=v_id,
                    recognized_text=recognized_text,
                    confidence=ocr_conf,
                    engine_name=self.engine_name,
                    timestamp=context.timestamp,
                    frame_id=context.frame_id
                )

                verified_number = None
                raw_txt = ""
                conf_val = 0.0
                val_status = "Unknown"
                status_str = "Processing"

                if rec_state is not None:
                    verified_number = plate_recognition_service.get_stable_plate(v_id)
                    best_cand = rec_state.best_candidate
                    
                    raw_txt = best_cand.normalized_text if best_cand else ""
                    conf_val = rec_state.aggregated_confidence
                    val_status = rec_state.validation_status

                    if verified_number is not None:
                        status_str = "Verified"
                        results["verified_count"] += 1
                    else:
                        if val_status == "Invalid":
                            results["rejected_count"] += 1
                            status_str = "Invalid"
                else:
                    if ocr_conf > 0.0:
                        raw_txt = recognized_text
                        conf_val = ocr_conf

                confidences_list.append(conf_val)

                det_res = DetectionResult(
                    module_name="ocr",
                    tracking_id=v_id,
                    vehicle_class=int(assoc.vehicle_class),
                    status=status_str,
                    confidence=conf_val,
                    timestamp=context.timestamp,
                    frame_id=context.frame_id,
                    region=assoc.vehicle_bbox,
                    metadata={
                        "raw_text": raw_txt,
                        "verified_text": verified_number or "",
                        "ocr_confidence": conf_val,
                        "validation_status": val_status,
                        "stable_plate": verified_number or "",
                        "engine_name": self.engine_name
                    }
                )
                ocr_results[v_id] = det_res.to_dict()

                # 4. Draw overlay visualization
                if context.working_frame is not None:
                    self._draw_overlay(context.working_frame, assoc.vehicle_bbox, v_id, status_str, verified_number or raw_txt, val_status)

            context.metadata["ocr"] = ocr_results

            # 5. Populate context stats
            avg_conf = float(np.mean(confidences_list)) if confidences_list else 0.0
            results["avg_confidence"] = avg_conf

            context.detection_counts["ocr_requests"] = results["requests_count"]
            context.detection_counts["ocr_verified"] = results["verified_count"]
            context.detection_counts["ocr_rejected"] = results["rejected_count"]
            context.detection_counts["ocr_avg_conf"] = int(avg_conf * 100)

        except Exception as e:
            logger.exception(f"LicensePlateOCRModule process error: {e}")
            errors.append({"module": "ocr", "message": str(e)})

        return results, errors, warnings

    def _draw_overlay(self, img: np.ndarray, vehicle_box: List[float], v_id: int, status_str: str, text: str, val_status: str) -> None:
        """Draws OCR labels above the vehicle bounding box."""
        vx1, vy1, vx2, vy2 = map(int, vehicle_box)

        # Colors (BGR)
        colors = {
            "Verified": (129, 185, 16),     # Green
            "Processing": (16, 185, 245),   # Yellow
            "Invalid": (68, 68, 239)        # Red
        }

        color = colors.get(status_str, (150, 150, 150))
        if val_status == "Invalid":
            color = colors["Invalid"]

        label_text = f"Vehicle #{v_id}: "
        if status_str == "Verified":
            label_text += f"PLATE {text} (VERIFIED)"
        else:
            label_text += f"OCR: {text or 'READING...'}"

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.35
        thickness = 1

        (w, h), _ = cv2.getTextSize(label_text, font, font_scale, thickness)
        tx = vx1
        ty = max(h + 20, vy1 - 18)  # Draw slightly above the ANPR box

        cv2.rectangle(img, (tx, ty - h - 4), (tx + w + 4, ty + 2), color, -1)
        cv2.putText(img, label_text, (tx + 2, ty - 2), font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)

    def shutdown(self) -> None:
        self._initialized = False
        self.reader = None
        logger.info("License Plate OCR Module shut down.")

    def health(self) -> bool:
        return self._initialized

    def status(self) -> Dict[str, Any]:
        return {
            "name": "LicensePlateOCRModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "config": self.config
        }
