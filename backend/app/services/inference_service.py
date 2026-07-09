"""
Inference Service — YOLOv8n detection.

Responsibilities:
  1. detect_raw()   → Run YOLO, return sv.Detections (no drawing).
  2. draw_tracked() → Receive tracked sv.Detections (with tracker_id),
                      draw bounding boxes, labels and IDs on the frame.

Keeping detection and rendering separate lets the TrackingService sit
cleanly between the two stages.
"""
import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO
from loguru import logger
from typing import Tuple, Dict


# COCO class index → display name (only vehicle classes we care about)
ALLOWED_CLASSES: Dict[int, str] = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Per-class BGR colours for bounding boxes
COLOR_MAP: Dict[str, Tuple[int, int, int]] = {
    "person":     (212, 182,   6),   # Cyan
    "bicycle":    (246, 130,  59),   # Blue
    "motorcycle": ( 11, 158, 245),   # Amber
    "car":        (129, 185,  16),   # Emerald
    "bus":        (246,  92, 139),   # Violet
    "truck":      ( 72, 236, 153),   # Pink
}


class InferenceService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: str = "models/pretrained/yolov8n.pt"):
        if self._initialized:
            return
        self._initialized = True
        self.model_path = model_path
        self.model: YOLO | None = None
        self._load_model()

    def _load_model(self):
        logger.info(f"Loading YOLOv8 model from '{self.model_path}'…")
        try:
            self.model = YOLO(self.model_path)
            logger.info("YOLOv8 model loaded successfully.")
        except Exception as e:
            logger.critical(f"Failed to load YOLOv8 model: {e}")
            raise

    # ------------------------------------------------------------------
    # Stage 1 — Raw detection (no drawing)
    # ------------------------------------------------------------------

    def detect_raw(
        self, frame: np.ndarray
    ) -> Tuple[sv.Detections, Dict[str, int]]:
        """
        Run YOLOv8 on `frame` and return:
            detections  — sv.Detections filtered to ALLOWED_CLASSES
            counts      — per-class + total_vehicles counts dict
        """
        empty = sv.Detections.empty()
        counts: Dict[str, int] = {k: 0 for k in COLOR_MAP}
        counts["total_vehicles"] = 0

        if self.model is None or frame is None:
            return empty, counts

        try:
            results = self.model(frame, verbose=False)
        except Exception as e:
            logger.error(f"YOLO inference error: {e}")
            return empty, counts

        if not results:
            return empty, counts

        result = results[0]
        boxes = result.boxes

        # Collect filtered detections
        xyxy_list, conf_list, cls_list = [], [], []

        for box in boxes:
            cls_idx = int(box.cls[0].item())
            if cls_idx not in ALLOWED_CLASSES:
                continue
            xyxy_list.append(box.xyxy[0].tolist())
            conf_list.append(float(box.conf[0].item()))
            cls_list.append(cls_idx)

            cls_name = ALLOWED_CLASSES[cls_idx]
            counts[cls_name] = counts.get(cls_name, 0) + 1
            if cls_name in ("car", "motorcycle", "truck", "bus", "bicycle"):
                counts["total_vehicles"] += 1

        if not xyxy_list:
            return empty, counts

        detections = sv.Detections(
            xyxy=np.array(xyxy_list, dtype=np.float32),
            confidence=np.array(conf_list, dtype=np.float32),
            class_id=np.array(cls_list, dtype=int),
        )
        return detections, counts

    # ------------------------------------------------------------------
    # Stage 2 — Draw tracked detections on frame
    # ------------------------------------------------------------------

    def draw_tracked(
        self, frame: np.ndarray, detections: sv.Detections
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels (class · ID · confidence) for every
        detection in `detections`. If `tracker_id` is available, show it.
        """
        if detections is None or len(detections) == 0:
            return frame

        drawn = frame.copy()

        for i in range(len(detections)):
            x1, y1, x2, y2 = map(int, detections.xyxy[i])
            cls_idx = int(detections.class_id[i])
            confidence = float(detections.confidence[i])
            cls_name = ALLOWED_CLASSES.get(cls_idx, f"class_{cls_idx}")

            # Tracking ID
            track_id = None
            if detections.tracker_id is not None:
                track_id = int(detections.tracker_id[i])

            color = COLOR_MAP.get(cls_name, (255, 255, 255))

            # Bounding box
            cv2.rectangle(drawn, (x1, y1), (x2, y2), color, 2)

            # Label text
            if track_id is not None:
                label = f"{cls_name.capitalize()} #{track_id}  {confidence:.0%}"
            else:
                label = f"{cls_name}  {confidence:.0%}"

            (tw, th), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1
            )
            # Label background pill
            cv2.rectangle(
                drawn,
                (x1, y1 - th - 7),
                (x1 + tw + 4, y1),
                color,
                -1,
            )
            cv2.putText(
                drawn,
                label,
                (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (255, 255, 255),
                1,
                lineType=cv2.LINE_AA,
            )

        return drawn


# Global singleton
inference_service = InferenceService()
