"""
Triple Riding Detection AI Module
=================================
Evaluates MotorcycleGroup counts from RiderAssociationService, applies temporal
gating, and triggers state transitions using confirmation buffers.
"""
import os
import cv2
import yaml
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from loguru import logger

from ai.pipelines.base_module import BaseAIModule
from ai.pipelines.pipeline_context import PipelineContext
from ai.services.rider_association_service import rider_association_service
from ai.services.trajectory_service import trajectory_service
from shared.schemas import DetectionResult


class TripleRidingDetectionModule(BaseAIModule):
    """
    YOLOv8-ByteTrack + RiderAssociationService occupant counting module.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.config: Dict[str, Any] = {}
        # Temporal buffers for confirmations
        self.single_confirmations: Dict[int, int] = {}
        self.double_confirmations: Dict[int, int] = {}
        self.triple_confirmations: Dict[int, int] = {}
        # Stable states
        self.stable_states: Dict[int, str] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Load configuration thresholds and reset tracking buffers."""
        if self._initialized:
            return

        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                self.config = full_cfg.get("modules", {}).get("triple_riding_detection", {})
                logger.info("Triple Riding Detection module configuration loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load configs from {self.pipeline_config_path}: {e}")
                self.config = {}
        else:
            logger.warning(f"{self.pipeline_config_path} not found. Using defaults.")
            self.config = {}

        self.single_confirmations.clear()
        self.double_confirmations.clear()
        self.triple_confirmations.clear()
        self.stable_states.clear()
        self._initialized = True
        logger.info("Triple Riding Detection module initialized.")

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Pulls associated motorcycle groups, performs temporal validation gates,
        maintains status buffers, and returns Pydantic DetectionResults.
        """
        errors = []
        warnings = []
        results = {
            "single_count": 0,
            "double_count": 0,
            "triple_count": 0,
            "unknown_count": 0,
            "status": "Inactive"
        }

        if not self._initialized:
            warnings.append({"module": "triple_riding_detection", "message": "Module not initialized."})
            return results, errors, warnings

        if context.tracked_detections is None:
            results["status"] = "Active"
            return results, errors, warnings

        results["status"] = "Active"

        try:
            # Resolve thresholds
            min_assoc_conf = self.config.get("minimum_association_confidence", 0.60)
            min_visible = self.config.get("minimum_visible_riders", 1)
            min_track_age = self.config.get("minimum_track_age", 5)
            confirm_frames = self.config.get("confirmation_frames", 3)

            tracked = context.tracked_detections
            active_ids = []
            triple_riding_stats = {}

            if tracked.xyxy is not None and tracked.tracker_id is not None:
                for box, track_id, class_id, conf in zip(
                    tracked.xyxy.tolist(),
                    tracked.tracker_id.tolist(),
                    tracked.class_id.tolist() if tracked.class_id is not None else [-1] * len(tracked.xyxy),
                    tracked.confidence.tolist() if tracked.confidence is not None else [1.0] * len(tracked.xyxy)
                ):
                    # Only evaluate motorcycle track objects (class_id == 3)
                    if class_id != 3:
                        continue

                    active_ids.append(track_id)

                    # 1. Fetch MotorcycleGroup from RiderAssociationService
                    group = rider_association_service.get_motorcycle_group(track_id)
                    state = trajectory_service.get_motion_state(track_id)
                    
                    track_age = state.track_age if state else 0
                    
                    # 2. Perform validation gates
                    validated = (
                        group is not None and
                        conf >= min_assoc_conf and
                        group.rider_count >= min_visible and
                        track_age >= min_track_age
                    )

                    current_state = "Unknown"

                    if validated and group:
                        r_count = group.rider_count
                        if r_count == 1:
                            raw_state = "Single Rider"
                        elif r_count == 2:
                            raw_state = "Double Riding"
                        elif r_count >= 3:
                            raw_state = "Triple Riding"
                        else:
                            raw_state = "Unknown"

                        # 3. Apply temporal confirmations smoothing
                        if raw_state == "Triple Riding":
                            self.triple_confirmations[track_id] = self.triple_confirmations.get(track_id, 0) + 1
                            self.double_confirmations[track_id] = 0
                            self.single_confirmations[track_id] = 0
                            if self.triple_confirmations[track_id] >= confirm_frames:
                                self.stable_states[track_id] = "Triple Riding"
                        elif raw_state == "Double Riding":
                            self.double_confirmations[track_id] = self.double_confirmations.get(track_id, 0) + 1
                            self.triple_confirmations[track_id] = 0
                            self.single_confirmations[track_id] = 0
                            if self.double_confirmations[track_id] >= confirm_frames:
                                self.stable_states[track_id] = "Double Riding"
                        elif raw_state == "Single Rider":
                            self.single_confirmations[track_id] = self.single_confirmations.get(track_id, 0) + 1
                            self.triple_confirmations[track_id] = 0
                            self.double_confirmations[track_id] = 0
                            if self.single_confirmations[track_id] >= confirm_frames:
                                self.stable_states[track_id] = "Single Rider"
                        else:
                            self.single_confirmations[track_id] = 0
                            self.double_confirmations[track_id] = 0
                            self.triple_confirmations[track_id] = 0

                        current_state = self.stable_states.get(track_id, "Unknown")

                    # 4. Standardized DetectionResult
                    driver_id = group.driver.rider_tracking_id if (group and group.driver) else None
                    passenger_ids = [p.rider_tracking_id for p in group.passengers] if group else []

                    det_res = DetectionResult(
                        module_name="triple_riding_detection",
                        tracking_id=track_id,
                        vehicle_class=int(class_id),
                        region=box,
                        status=current_state,
                        confidence=float(conf),
                        timestamp=context.timestamp,
                        frame_id=context.frame_id,
                        metadata={
                            "rider_count": group.rider_count if group else 0,
                            "driver_id": driver_id,
                            "passenger_ids": passenger_ids,
                            "motorcycle_group_id": track_id
                        }
                    )
                    triple_riding_stats[track_id] = det_res.to_dict()

                    # Aggregate status counters
                    if current_state == "Single Rider":
                        results["single_count"] += 1
                    elif current_state == "Double Riding":
                        results["double_count"] += 1
                    elif current_state == "Triple Riding":
                        results["triple_count"] += 1
                    else:
                        results["unknown_count"] += 1

                    # 5. Draw overlays
                    if context.working_frame is not None:
                        self._draw_overlay(context.working_frame, box, track_id, current_state, group)

            context.metadata["triple_riding_detection"] = triple_riding_stats

            # Sync with context counts
            context.detection_counts["single_rider"] = results["single_count"]
            context.detection_counts["double_riding"] = results["double_count"]
            context.detection_counts["triple_riding"] = results["triple_count"]
            context.detection_counts["triple_unknown"] = results["unknown_count"]

            self._cleanup_inactive_buffers(active_ids)

        except Exception as e:
            logger.exception(f"TripleRidingDetectionModule error: {e}")
            errors.append({"module": "triple_riding_detection", "message": str(e)})

        return results, errors, warnings

    def _draw_overlay(self, img: np.ndarray, box: List[float], track_id: int, status_val: str, group: Optional[Any]) -> None:
        """Draw overlays showing motorcycle ID, rider count, driver, passengers, status, and confidence."""
        x1, y1, x2, y2 = map(int, box)

        # Colors (BGR)
        colors = {
            "Single Rider": (129, 185, 16),   # Green
            "Double Riding": (16, 185, 245),  # Yellow
            "Triple Riding": (68, 68, 239),   # Red
            "Unknown": (150, 150, 150)        # Gray
        }

        color = colors.get(status_val, colors["Unknown"])
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Draw associated riders boxes
        if group:
            if group.driver:
                rx1, ry1, rx2, ry2 = map(int, group.driver.bounding_box)
                cv2.rectangle(img, (rx1, ry1), (rx2, ry2), (255, 200, 0), 1) # Cyan-blue for occupants
            for p in group.passengers:
                rx1, ry1, rx2, ry2 = map(int, p.bounding_box)
                cv2.rectangle(img, (rx1, ry1), (rx2, ry2), (255, 150, 0), 1)

        # Banner text
        r_count = group.rider_count if group else 0
        label_text = f"Moto #{track_id}: "
        if status_val == "Triple Riding":
            label_text += f"TRIPLE RIDING ❌ ({r_count} Riders)"
        elif status_val == "Double Riding":
            label_text += f"DOUBLE ({r_count} Riders)"
        elif status_val == "Single Rider":
            label_text += f"SINGLE ({r_count} Rider)"
        else:
            label_text += f"UNKNOWN ⚪"

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.35
        thickness = 1

        (w, h), _ = cv2.getTextSize(label_text, font, font_scale, thickness)
        tx = x1
        ty = max(h + 6, y1 - 4)

        cv2.rectangle(img, (tx, ty - h - 4), (tx + w + 4, ty + 2), color, -1)
        cv2.putText(img, label_text, (tx + 2, ty - 2), font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)

    def _cleanup_inactive_buffers(self, active_ids: List[int]) -> None:
        """Cleanup trackers that left the frame."""
        for vid in list(self.single_confirmations.keys()):
            if vid not in active_ids:
                self.single_confirmations.pop(vid, None)
                self.double_confirmations.pop(vid, None)
                self.triple_confirmations.pop(vid, None)
                self.stable_states.pop(vid, None)

    def shutdown(self) -> None:
        self.single_confirmations.clear()
        self.double_confirmations.clear()
        self.triple_confirmations.clear()
        self.stable_states.clear()
        self._initialized = False
        logger.info("Triple Riding Detection module shut down.")

    def health(self) -> bool:
        return self._initialized

    def status(self) -> Dict[str, Any]:
        return {
            "name": "TripleRidingDetectionModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "config": self.config
        }
