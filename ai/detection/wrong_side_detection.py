"""
Wrong Side Detection AI Module
==============================
Rule-based evaluation of vehicle travel directions using TrajectoryService,
MotionState metrics, and RoadSceneService orientations with temporal smoothing.
"""
import os
import cv2
import yaml
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from loguru import logger

from ai.pipelines.base_module import BaseAIModule
from ai.pipelines.pipeline_context import PipelineContext
from ai.services.road_scene_service import RoadSceneService
from ai.services.trajectory_service import trajectory_service
from shared.schemas import DetectionResult


class WrongSideDetectionModule(BaseAIModule):
    """
    Evaluates tracking trajectories to detect vehicles driving against the lane direction.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.config: Dict[str, Any] = {}
        # Temporal smoothing buffers: tracking_id -> consecutive hits count
        self.wrong_confirmations: Dict[int, int] = {}
        self.correct_confirmations: Dict[int, int] = {}
        # Stable confirmed states: tracking_id -> 'Wrong Side' or 'Correct Direction'
        self.stable_states: Dict[int, str] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Load configuration thresholds and reset tracking buffers."""
        if self._initialized:
            return

        # Load thresholds from pipeline.yaml
        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                self.config = full_cfg.get("modules", {}).get("wrong_side_detection", {})
                logger.info("Wrong Side Detection module configuration loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading {self.pipeline_config_path}: {e}. Using default thresholds.")
                self.config = {}
        else:
            logger.warning(f"Configuration file {self.pipeline_config_path} not found. Using defaults.")
            self.config = {}

        self.wrong_confirmations.clear()
        self.correct_confirmations.clear()
        self.stable_states.clear()
        self._initialized = True
        logger.info("Wrong Side Detection module initialized.")

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extracts MotionState objects for active tracked vehicles, performs
        temporal validation, compares direction angles, and records outcomes.
        """
        errors = []
        warnings = []
        results = {
            "wrong_side_count": 0,
            "correct_direction_count": 0,
            "unknown_count": 0,
            "status": "Inactive"
        }

        if not self._initialized:
            warnings.append({"module": "wrong_side_detection", "message": "Module not initialized."})
            return results, errors, warnings

        # If tracking detections are missing in context, skip execution
        if context.tracked_detections is None:
            results["status"] = "Active"
            return results, errors, warnings

        results["status"] = "Active"

        try:
            # Resolve thresholds dynamically
            min_track_age = self.config.get("minimum_track_age", 10)
            min_distance = self.config.get("minimum_distance", 30.0)
            min_angle_diff = self.config.get("minimum_angle_difference", 135.0)
            min_history = self.config.get("minimum_history", 5)
            min_motion_conf = self.config.get("minimum_motion_confidence", 0.70)
            consec_confirmations = self.config.get("consecutive_confirmations", 3)

            tracked = context.tracked_detections
            
            # Fetch active track IDs to clean up local buffer garbage later
            active_ids = []
            wrong_side_stats = {}

            if tracked.xyxy is not None and tracked.tracker_id is not None:
                for box, track_id, class_id, conf in zip(
                    tracked.xyxy.tolist(),
                    tracked.tracker_id.tolist(),
                    tracked.class_id.tolist() if tracked.class_id is not None else [-1] * len(tracked.xyxy),
                    tracked.confidence.tolist() if tracked.confidence is not None else [1.0] * len(tracked.xyxy)
                ):
                    active_ids.append(track_id)

                    # 1. Fetch MotionState from global TrajectoryService
                    state = trajectory_service.get_motion_state(track_id)
                    if state is None:
                        logger.warning(f"MotionState missing for tracked vehicle ID {track_id}")
                        current_state = "Unknown"
                    else:
                        # 2. Perform temporal validation criteria checks
                        validated = (
                            state.track_age >= min_track_age and
                            state.total_distance >= min_distance and
                            state.history_length >= min_history and
                            state.confidence >= min_motion_conf
                        )

                        current_state = "Unknown"

                        if validated and state.travel_angle is not None:
                            # 3. Fetch lane orientation angle from central RoadSceneService
                            # Default lane_id = 0, expected direction = 90.0 degrees (downward flow)
                            expected_angle = RoadSceneService.get_lane_orientation(lane_id=0)
                            
                            # Compare heading angles
                            diff = abs(state.travel_angle - expected_angle) % 360
                            diff = min(diff, 360 - diff)

                            raw_classification = "Wrong Side" if diff > min_angle_diff else "Correct Direction"

                            # 4. Temporal confirmations smoothing
                            if raw_classification == "Wrong Side":
                                self.wrong_confirmations[track_id] = self.wrong_confirmations.get(track_id, 0) + 1
                                self.correct_confirmations[track_id] = 0
                                if self.wrong_confirmations[track_id] >= consec_confirmations:
                                    self.stable_states[track_id] = "Wrong Side"
                            else:
                                self.correct_confirmations[track_id] = self.correct_confirmations.get(track_id, 0) + 1
                                self.wrong_confirmations[track_id] = 0
                                if self.correct_confirmations[track_id] >= consec_confirmations:
                                    self.stable_states[track_id] = "Correct Direction"

                            current_state = self.stable_states.get(track_id, "Unknown")

                    # 5. Populate standardized DetectionResult
                    det_res = DetectionResult(
                        module_name="wrong_side_detection",
                        tracking_id=track_id,
                        vehicle_class=int(class_id),
                        region=box,
                        status=current_state,
                        confidence=float(conf),
                        timestamp=context.timestamp,
                        frame_id=context.frame_id,
                        metadata={
                            "travel_angle": float(state.travel_angle) if (state and state.travel_angle is not None) else None,
                            "stable_confirmations": int(self.wrong_confirmations.get(track_id, 0)) if current_state == "Wrong Side" else int(self.correct_confirmations.get(track_id, 0))
                        }
                    )
                    wrong_side_stats[track_id] = det_res.to_dict()

                    # Update local metrics counters
                    if current_state == "Wrong Side":
                        results["wrong_side_count"] += 1
                    elif current_state == "Correct Direction":
                        results["correct_direction_count"] += 1
                    else:
                        results["unknown_count"] += 1

                    # 6. Draw visual overlays
                    if context.working_frame is not None:
                        self._draw_overlay(context.working_frame, box, track_id, current_state, float(conf))

            context.metadata["wrong_side_detection"] = wrong_side_stats

            # Sync totals with context metrics counters
            context.detection_counts["wrong_side"] = results["wrong_side_count"]
            context.detection_counts["correct_direction"] = results["correct_direction_count"]
            context.detection_counts["wrong_side_unknown"] = results["unknown_count"]

            # Cleanup inactive IDs from buffers
            self._cleanup_inactive_buffers(active_ids)

        except Exception as e:
            logger.exception(f"WrongSideDetectionModule execution error: {e}")
            errors.append({"module": "wrong_side_detection", "message": str(e)})

        return results, errors, warnings

    def _draw_overlay(self, img: np.ndarray, box: List[float], track_id: int, status_val: str, conf: float):
        """Draw bounding boxes and travel banners with orientation indicators."""
        x1, y1, x2, y2 = map(int, box)

        # Colors (BGR)
        colors = {
            "Correct Direction": (129, 185, 16),   # Green
            "Wrong Side": (68, 68, 239),           # Red
            "Unknown": (150, 150, 150)             # Gray
        }

        color = colors.get(status_val, colors["Unknown"])
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Banners text: ID + travel state
        label_text = f"Vehicle #{track_id}: "
        if status_val == "Wrong Side":
            label_text += "WRONG SIDE ❌"
        elif status_val == "Correct Direction":
            label_text += "CORRECT ✅"
        else:
            label_text += "UNKNOWN ⚪"

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.35
        thickness = 1

        (w, h), _ = cv2.getTextSize(label_text, font, font_scale, thickness)
        tx = x1
        ty = max(h + 6, y1 - 4)

        cv2.rectangle(img, (tx, ty - h - 4), (tx + w + 4, ty + 2), color, -1)
        cv2.putText(img, label_text, (tx + 2, ty - 2), font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)

    def _cleanup_inactive_buffers(self, active_ids: List[int]) -> None:
        """Removes local confirmations for vehicles that left the frame."""
        for vid in list(self.wrong_confirmations.keys()):
            if vid not in active_ids:
                self.wrong_confirmations.pop(vid, None)
                self.correct_confirmations.pop(vid, None)
                self.stable_states.pop(vid, None)

    def shutdown(self) -> None:
        self.wrong_confirmations.clear()
        self.correct_confirmations.clear()
        self.stable_states.clear()
        self._initialized = False
        logger.info("Wrong Side Detection module shut down.")

    def health(self) -> bool:
        return self._initialized

    def status(self) -> Dict[str, Any]:
        return {
            "name": "WrongSideDetectionModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "config": self.config
        }
