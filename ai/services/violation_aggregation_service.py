"""
Violation Aggregation Service
=============================
Consolidates frame-level outputs from all AI modules per tracked vehicle,
maintains historical logs, computes temporal/confidence aggregates, and builds
a unified VehicleViolationContext.
"""
import os
import yaml
import time
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from shared.schemas.violation_context import VehicleViolationContext, ViolationHistoryEntry
from ai.services.road_scene_service import RoadSceneService
from ai.services.plate_recognition_service import plate_recognition_service
from ai.pipelines.pipeline_context import PipelineContext


class ViolationAggregationService:
    """
    Unified manager for consolidating detection results into vehicle violation contexts.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.config: Dict[str, Any] = {}
        # contexts maps vehicle_tracking_id -> VehicleViolationContext
        self.contexts: Dict[int, VehicleViolationContext] = {}
        self.load_config()

    def load_config(self) -> None:
        """Loads configuration from pipeline.yaml, falling back to default thresholds."""
        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                self.config = full_cfg.get("modules", {}).get("violation_aggregation", {})
            except Exception as e:
                logger.error(f"Failed to load ViolationAggregationService configs: {e}")
                self.config = {}

        # Default configuration values
        self.history_length = self.config.get("history_length", 20)
        self.minimum_confidence = self.config.get("minimum_confidence", 0.50)
        self.minimum_frames = self.config.get("minimum_frames", 3)
        self.context_timeout = self.config.get("context_timeout", 5.0)
        self.maximum_history = self.config.get("maximum_history", 50)
        self.aggregation_weights = self.config.get(
            "aggregation_weights",
            {
                "helmet": 0.80,
                "seatbelt": 0.80,
                "phone": 0.85,
                "wrong_side": 0.90,
                "signal": 0.90,
                "triple_riding": 0.85
            }
        )

    def update_detection(
        self,
        tracking_id: int,
        module_name: str,
        status: str,
        confidence: float,
        timestamp: float,
        frame_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Public API to update the violation context of a vehicle with a single module's output.
        """
        # Ensure context exists
        if tracking_id not in self.contexts:
            # We need a vehicle class fallback. If class is not yet known, set to -1
            self.contexts[tracking_id] = VehicleViolationContext(
                tracking_id=tracking_id,
                vehicle_class=-1,
                timestamp=timestamp,
                frame_id=frame_id,
                first_seen=timestamp,
                last_seen=timestamp,
                frame_count=1
            )
            logger.info(f"Violation Context Created for Vehicle #{tracking_id}")

        ctx = self.contexts[tracking_id]
        if ctx.frame_id != frame_id:
            ctx.frame_count += 1
        ctx.timestamp = timestamp
        ctx.frame_id = frame_id
        ctx.last_seen = timestamp

        # Clean/Normalize input status
        status = status.strip() if status else "Unknown"

        # Check duplicate frame matching for the same module
        is_duplicate = False
        if ctx.violation_history:
            last_entry = ctx.violation_history[-1]
            if last_entry.module_name == module_name and last_entry.frame_id == frame_id:
                is_duplicate = True

        # Append to history if it represents a potential violation and not a duplicate
        is_violation = status in (
            "No Helmet",
            "No Seat Belt",
            "Mobile Phone",
            "Wrong Side",
            "Red Light Jump",
            "Triple Riding"
        )
        if is_violation and not is_duplicate:
            entry = ViolationHistoryEntry(
                module_name=module_name,
                status=status,
                confidence=confidence,
                timestamp=timestamp,
                frame_id=frame_id,
                tracking_id=tracking_id,
                metadata=metadata or {}
            )
            ctx.violation_history.append(entry)
            # Limit history length
            if len(ctx.violation_history) > self.maximum_history:
                ctx.violation_history.pop(0)

        # Update specific module status and confidence fields
        if module_name == "helmet_detection":
            ctx.helmet_status = status
            ctx.helmet_confidence = confidence
        elif module_name == "seat_belt_detection":
            ctx.seatbelt_status = status
            ctx.seatbelt_confidence = confidence
        elif module_name in ("phone_detection", "mobile_phone_detection"):
            ctx.phone_status = status
            ctx.phone_confidence = confidence
        elif module_name == "wrong_side_detection":
            ctx.wrong_side_status = status
            ctx.wrong_side_confidence = confidence
        elif module_name == "triple_riding_detection":
            ctx.triple_riding_status = status
            ctx.triple_riding_confidence = confidence
        elif module_name == "traffic_signal_detection":
            ctx.signal_status = status
            ctx.signal_confidence = confidence

        # Perform context aggregation updates
        self._aggregate_context(ctx)

    def update_from_context(self, context: PipelineContext) -> None:
        """
        Automated entry point called by the Pipeline Manager at Stage 6.
        Scans tracking detections and active module metadata to update all vehicle contexts.
        """
        if context.tracked_detections is None:
            return

        active_tracking_ids = []
        frame_id = context.frame_id
        timestamp = context.timestamp

        tracked = context.tracked_detections
        if tracked.xyxy is not None and tracked.tracker_id is not None:
            for box, track_id, class_id in zip(
                tracked.xyxy.tolist(),
                tracked.tracker_id.tolist(),
                tracked.class_id.tolist() if tracked.class_id is not None else [-1] * len(tracked.xyxy)
            ):
                track_id = int(track_id)
                active_tracking_ids.append(track_id)

                # 1. Initialize or get context
                if track_id not in self.contexts:
                    self.contexts[track_id] = VehicleViolationContext(
                        tracking_id=track_id,
                        vehicle_class=int(class_id),
                        timestamp=timestamp,
                        frame_id=frame_id,
                        first_seen=timestamp,
                        last_seen=timestamp,
                        frame_count=0
                    )
                    logger.info(f"Violation Context Created for Vehicle #{track_id}")

                ctx = self.contexts[track_id]
                ctx.vehicle_class = int(class_id)
                ctx.last_seen = timestamp
                ctx.frame_count += 1
                ctx.timestamp = timestamp
                ctx.frame_id = frame_id

                # 2. Update verified plate text if available
                verified_plate = plate_recognition_service.get_stable_plate(track_id)
                if verified_plate:
                    ctx.verified_plate = verified_plate

                # 3. Pull module detections from context metadata
                # Helmet
                helmet_data = context.metadata.get("helmet_detection", {}).get(track_id)
                if helmet_data:
                    self.update_detection(
                        track_id, "helmet_detection", helmet_data["status"],
                        helmet_data["confidence"], timestamp, frame_id, helmet_data.get("metadata")
                    )

                # Seat Belt
                sb_data = context.metadata.get("seat_belt_detection", {}).get(track_id)
                if sb_data:
                    self.update_detection(
                        track_id, "seat_belt_detection", sb_data["status"],
                        sb_data["confidence"], timestamp, frame_id, sb_data.get("metadata")
                    )

                # Mobile Phone
                mp_data = context.metadata.get("mobile_phone_detection", {}).get(track_id)
                if mp_data:
                    self.update_detection(
                        track_id, "mobile_phone_detection", mp_data["status"],
                        mp_data["confidence"], timestamp, frame_id, mp_data.get("metadata")
                    )

                # Wrong Side
                ws_data = context.metadata.get("wrong_side_detection", {}).get(track_id)
                if ws_data:
                    self.update_detection(
                        track_id, "wrong_side_detection", ws_data["status"],
                        ws_data["confidence"], timestamp, frame_id, ws_data.get("metadata")
                    )

                # Triple Riding
                tr_data = context.metadata.get("triple_riding_detection", {}).get(track_id)
                if tr_data:
                    self.update_detection(
                        track_id, "triple_riding_detection", tr_data["status"],
                        tr_data["confidence"], timestamp, frame_id, tr_data.get("metadata")
                    )

                # 4. Evaluate Stop Line red light jump
                signal_stats = context.metadata.get("traffic_signal_detection", {})
                is_light_red = False
                red_light_conf = 0.0
                for sig_id, sig_data in signal_stats.items():
                    if sig_data.get("status") == "Red":
                        is_light_red = True
                        red_light_conf = max(red_light_conf, sig_data.get("confidence", 0.0))

                if is_light_red:
                    w = context.raw_frame.shape[1] if context.raw_frame is not None else 1920
                    h = context.raw_frame.shape[0] if context.raw_frame is not None else 1080
                    stop_line_roi = RoadSceneService.get_stop_line_roi(w, h)
                    
                    if RoadSceneService.is_in_roi(box, stop_line_roi):
                        self.update_detection(
                            track_id, "traffic_signal_detection", "Red Light Jump",
                            red_light_conf, timestamp, frame_id
                        )

        # 5. Clean up stale contexts (timeout disappeared vehicles)
        self.cleanup_stale_contexts(timestamp)

    def _aggregate_context(self, ctx: VehicleViolationContext) -> None:
        """
        Computes the temporal, confidence, stability, and verification states of a context.
        """
        # Determine active violations based on current status fields
        active_violation_confs = []
        
        status_map = {
            ctx.helmet_status: (ctx.helmet_confidence, "helmet"),
            ctx.seatbelt_status: (ctx.seatbelt_confidence, "seatbelt"),
            ctx.phone_status: (ctx.phone_confidence, "phone"),
            ctx.wrong_side_status: (ctx.wrong_side_confidence, "wrong_side"),
            ctx.signal_status: (ctx.signal_confidence, "signal"),
            ctx.triple_riding_status: (ctx.triple_riding_confidence, "triple_riding"),
        }

        for status, (conf, name) in status_map.items():
            is_viol = status in (
                "No Helmet",
                "No Seat Belt",
                "Mobile Phone",
                "Wrong Side",
                "Red Light Jump",
                "Triple Riding"
            )
            if is_viol and conf >= self.minimum_confidence:
                # Apply config weight to calculate weighted score
                weight = self.aggregation_weights.get(name, 1.0)
                active_violation_confs.append(conf * weight)

        # Compute final aggregated scores
        if active_violation_confs:
            max_weighted_conf = max(active_violation_confs)
            ctx.stable_detection = ctx.frame_count >= self.minimum_frames
            
            if ctx.stable_detection:
                ctx.verification_state = "Verified"
                ctx.evidence_ready = True
            else:
                ctx.verification_state = "Processing"
                ctx.evidence_ready = False
        else:
            # Check if any have "Unknown" or "Processing" style states
            non_unknown = [
                s for s in status_map.keys()
                if s not in ("Unknown", "Processing", "Normal", "Correct Direction", "Helmet", "Seat Belt")
            ]
            if non_unknown:
                ctx.verification_state = "Processing"
            else:
                ctx.verification_state = "No Violation"
            
            ctx.stable_detection = False
            ctx.evidence_ready = False

    def cleanup_stale_contexts(self, current_timestamp: float) -> None:
        """
        Removes vehicle contexts that haven't been seen/updated for longer than context_timeout.
        """
        to_remove = []
        for track_id, ctx in list(self.contexts.items()):
            if current_timestamp - ctx.last_seen > self.context_timeout:
                to_remove.append(track_id)

        for track_id in to_remove:
            self.remove_vehicle(track_id)

    def get_context(self, tracking_id: int) -> Optional[VehicleViolationContext]:
        return self.contexts.get(tracking_id)

    def get_vehicle_context(self, tracking_id: int) -> Optional[VehicleViolationContext]:
        return self.get_context(tracking_id)

    def get_all_contexts(self) -> List[VehicleViolationContext]:
        return list(self.contexts.values())

    def clear_context(self, tracking_id: int) -> None:
        if tracking_id in self.contexts:
            del self.contexts[tracking_id]
            logger.info(f"Context cleared for Vehicle #{tracking_id}")

    def remove_vehicle(self, tracking_id: int) -> None:
        if tracking_id in self.contexts:
            del self.contexts[tracking_id]
            logger.info(f"Context removed/cleaned up for Vehicle #{tracking_id}")

    def reset(self) -> None:
        self.contexts.clear()
        logger.info("ViolationAggregationService cache reset.")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Computes active aggregation statistics for camera diagnostics and analytics.
        """
        total_tracked = len(self.contexts)
        violations = {
            "no_helmet": 0,
            "no_seatbelt": 0,
            "phone_usage": 0,
            "wrong_side": 0,
            "red_light_jump": 0,
            "triple_riding": 0
        }
        verified_count = 0
        processing_count = 0

        for ctx in self.contexts.values():
            if ctx.verification_state == "Verified":
                verified_count += 1
            elif ctx.verification_state == "Processing":
                processing_count += 1

            if ctx.helmet_status == "No Helmet":
                violations["no_helmet"] += 1
            if ctx.seatbelt_status == "No Seat Belt":
                violations["no_seatbelt"] += 1
            if ctx.phone_status == "Mobile Phone":
                violations["phone_usage"] += 1
            if ctx.wrong_side_status == "Wrong Side":
                violations["wrong_side"] += 1
            if ctx.signal_status == "Red Light Jump":
                violations["red_light_jump"] += 1
            if ctx.triple_riding_status == "Triple Riding":
                violations["triple_riding"] += 1

        return {
            "total_tracked": total_tracked,
            "verified_violations": verified_count,
            "processing_violations": processing_count,
            "violations_breakdown": violations
        }


# Singleton service instance
violation_aggregation_service = ViolationAggregationService()
