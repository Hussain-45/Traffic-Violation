"""
AI Pipeline Manager
===================
Orchestrates the entire AI processing pipeline:
Validation -> Preprocessing -> YOLO -> ByteTrack -> Dispatcher -> Aggregation -> Visualization -> Output.
"""
import time
import os
import threading
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import yaml
from loguru import logger

from ai.pipelines.pipeline_context import PipelineContext
from ai.pipelines.result_object import PipelineResult
from ai.pipelines.registry import module_registry
from ai.pipelines.performance_monitor import PerformanceMonitor
from backend.app.services.inference_service import inference_service
from ai.services.violation_aggregation_service import violation_aggregation_service
from ai.violations.evidence_generator import evidence_generator
from shared.schemas.violation_record import ViolationRecord
from backend.app.services.database_service import database_service


class PipelineManager:
    """
    Centralized, thread-safe manager that orchestrates the execution of AI modules.
    Processes a frame through a sequence of validation, preprocessing, detection, tracking,
    dispatching, result aggregation, and visualization overlays.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PipelineManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_path: str = "configs/pipeline.yaml"):
        if self._initialized:
            return
        self._initialized = True
        self.config_path = config_path
        
        # Load configuration
        self.config: Dict[str, Any] = {}
        self.enabled_modules: List[str] = []
        self.execution_order: List[str] = []
        self.visualization_config: Dict[str, bool] = {}
        
        self.load_config()
        
        # Initialize registry & performance monitor
        self.performance_monitor = PerformanceMonitor()
        
        # Runtime lifecycle state
        self.is_running = False
        self.frame_counter = 0

        # Start the pipeline (initialize modules)
        self.start()

    def load_config(self):
        """Load pipeline configuration from YAML, falling back to defaults if not found."""
        default_config = {
            "debug_mode": True,
            "logging_level": "INFO",
            "execution_order": [
                "vehicle_detection", "vehicle_tracking", "helmet_detection",
                "seat_belt_detection", "phone_detection", "traffic_signal_detection",
                "wrong_side_detection", "number_plate_detection", "ocr", "violation_engine"
            ],
            "modules": {
                "vehicle_detection": {"enabled": True, "confidence_threshold": 0.45},
                "vehicle_tracking": {"enabled": True, "confidence_threshold": 0.45},
                "helmet_detection": {"enabled": False},
                "seat_belt_detection": {"enabled": False},
                "phone_detection": {"enabled": False},
                "traffic_signal_detection": {"enabled": False},
                "wrong_side_detection": {"enabled": False},
                "number_plate_detection": {"enabled": False},
                "ocr": {"enabled": False},
                "violation_engine": {"enabled": False},
            },
            "visualization": {
                "draw_boxes": True,
                "draw_ids": True,
                "draw_labels": True,
                "draw_roi": True,
                "draw_trails": False,
                "draw_heatmap": False
            }
        }

        if not os.path.exists(self.config_path):
            logger.warning(f"Pipeline config file not found at '{self.config_path}'. Using default config.")
            self.config = default_config
        else:
            try:
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f) or default_config
                logger.info(f"Pipeline configuration loaded from '{self.config_path}'.")
            except Exception as e:
                logger.error(f"Error loading pipeline configuration from '{self.config_path}': {e}. Using defaults.")
                self.config = default_config

        # Extract values
        self.execution_order = self.config.get("execution_order", [])
        self.visualization_config = self.config.get("visualization", {})
        
        # Build active modules list based on config enablement
        modules_cfg = self.config.get("modules", {})
        self.enabled_modules = [
            name for name in self.execution_order
            if modules_cfg.get(name, {}).get("enabled", False)
        ]
        
        # Log modules status once (not per frame)
        for name in self.execution_order:
            is_enabled = name in self.enabled_modules
            status_str = "Loaded" if is_enabled else "Disabled"
            logger.info(f"Pipeline Module: '{name}' is {status_str}")

    def start(self):
        """Start the pipeline manager, initializing all registered AI modules."""
        with self._lock:
            if self.is_running:
                return
            logger.info("Pipeline Manager starting...")
            module_registry.initialize_all()
            self.is_running = True
            logger.info("Pipeline Manager started successfully.")

    def stop(self):
        """Stop the pipeline manager, shutting down all registered AI modules."""
        with self._lock:
            if not self.is_running:
                return
            logger.info("Pipeline Manager stopping...")
            module_registry.shutdown_all()
            self.is_running = False
            logger.info("Pipeline Manager stopped.")

    def process_frame(
        self, frame: np.ndarray, frame_id: Optional[int] = None, timestamp: Optional[float] = None
    ) -> PipelineResult:
        """
        Process a single video frame through the 8 stages of the pipeline:
          1. Frame Validation
          2. Frame Preprocessing
          3. YOLO Detection (Vehicle Detection)
          4. ByteTrack Tracking (Vehicle Tracking)
          5. AI Module Dispatcher
          6. Result Aggregation
          7. Visualization Overlays (placeholders only)
          8. Output

        Parameters
        ----------
        frame     : OpenCV image frame as a NumPy array (BGR).
        frame_id  : Option frame identifier index. If None, incremented automatically.
        timestamp : Capture epoch timestamp. If None, defaults to current time.

        Returns
        -------
        PipelineResult: Standardized output container containing detections, timing, warning, and metadata.
        """
        t_start = time.time()
        
        # Resolve frame identity
        if frame_id is None:
            self.frame_counter += 1
            f_id = self.frame_counter
        else:
            f_id = frame_id
            
        ts = timestamp if timestamp is not None else time.time()
        
        # Initialize context
        context = PipelineContext(
            frame_id=f_id,
            timestamp=ts,
            raw_frame=frame,
            config=self.config
        )

        t_yolo = 0.0
        t_track = 0.0
        module_times = {}

        # -------------------------------------------------------------
        # Stage 1 — Frame Validation
        # -------------------------------------------------------------
        if not self._stage_validate_frame(frame, context):
            # Frame is dropped / invalid. Return early with empty result.
            t_end = time.time()
            total_duration = (t_end - t_start) * 1000.0
            return PipelineResult(
                frame_id=f_id,
                timestamp=ts,
                raw_frame=frame,
                visualized_frame=frame,
                timing={"pipeline_total_ms": total_duration},
                errors=context.errors,
                warnings=context.warnings,
                metadata=context.metadata,
                counts=context.detection_counts
            )

        # -------------------------------------------------------------
        # Stage 2 — Frame Preprocessing
        # -------------------------------------------------------------
        self._stage_preprocess_frame(context)

        # -------------------------------------------------------------
        # Stage 3 — YOLO Detection (Vehicle Detection module)
        # -------------------------------------------------------------
        if "vehicle_detection" in self.enabled_modules:
            t_stage_start = time.time()
            self._execute_module_safely("vehicle_detection", context)
            t_yolo = (time.time() - t_stage_start) * 1000.0
            module_times["vehicle_detection"] = t_yolo

        # -------------------------------------------------------------
        # Stage 4 — ByteTrack Tracking (Vehicle Tracking module)
        # -------------------------------------------------------------
        if "vehicle_tracking" in self.enabled_modules:
            t_stage_start = time.time()
            self._execute_module_safely("vehicle_tracking", context)
            t_track = (time.time() - t_stage_start) * 1000.0
            module_times["vehicle_tracking"] = t_track

        # -------------------------------------------------------------
        # Stage 5 — AI Module Dispatcher (helmet, seatbelt, etc.)
        # -------------------------------------------------------------
        # Loop through other enabled modules in the configured execution order
        for mod_name in self.execution_order:
            if mod_name in ("vehicle_detection", "vehicle_tracking"):
                # Done in dedicated stages 3 and 4
                continue
            if mod_name in self.enabled_modules:
                t_stage_start = time.time()
                self._execute_module_safely(mod_name, context)
                t_duration = (time.time() - t_stage_start) * 1000.0
                module_times[mod_name] = t_duration

        # -------------------------------------------------------------
        # Stage 6 — Result Aggregation
        # -------------------------------------------------------------
        # Consolidate results from module context.metadata into metadata
        violation_aggregation_service.update_from_context(context)
        
        # -------------------------------------------------------------
        # Stage 7 — Visualization (drawing placeholders)
        # -------------------------------------------------------------
        self._stage_visualize(context)

        # -------------------------------------------------------------
        # Stage 8 — Output
        # -------------------------------------------------------------
        # Generate evidence for confirmed violation records
        if "violation_engine" in context.metadata:
            records_dict = context.metadata["violation_engine"].get("records", [])
            violation_records = []
            for r_dict in records_dict:
                violation_records.append(ViolationRecord(**r_dict))
            
            if violation_records:
                evidence_records = evidence_generator.process_evidence(violation_records, context)
                context.metadata["evidence_records"] = [rec.to_dict() for rec in evidence_records]
                
                # Persist each record to the database
                for ev_rec in evidence_records:
                    try:
                        database_service.insert_evidence(ev_rec)
                    except Exception as e:
                        logger.error(f"Failed to persist evidence record {ev_rec.evidence_id} to database: {e}")

        t_end = time.time()
        total_duration = (t_end - t_start) * 1000.0
        
        # Record stats to Performance Monitor
        self.performance_monitor.record_frame(
            pipeline_time_ms=total_duration,
            yolo_time_ms=t_yolo,
            tracking_time_ms=t_track
        )
        for name, dur in module_times.items():
            self.performance_monitor.record_module(name, dur)

        # Compile timing dict for this frame
        all_timing = {
            "pipeline_total_ms": round(total_duration, 2),
            "yolo_time_ms": round(t_yolo, 2),
            "tracking_time_ms": round(t_track, 2),
        }
        for name, dur in module_times.items():
            all_timing[f"{name}_time_ms"] = round(dur, 2)

        # Return standardized PipelineResult
        return PipelineResult(
            frame_id=f_id,
            timestamp=ts,
            raw_frame=frame,
            visualized_frame=context.working_frame,
            detections=context.raw_detections,
            tracks=context.tracked_detections,
            timing=all_timing,
            errors=context.errors,
            warnings=context.warnings,
            metadata=context.metadata,
            counts=context.detection_counts
        )

    def _stage_validate_frame(self, frame: np.ndarray, context: PipelineContext) -> bool:
        """Stage 1: Verify the frame contains valid image data."""
        if frame is None:
            msg = "Received None frame. Dropping frame."
            logger.warning(msg)
            context.add_error("validation", msg)
            return False

        if not isinstance(frame, np.ndarray):
            msg = f"Invalid frame type: {type(frame)}. Dropping frame."
            logger.warning(msg)
            context.add_error("validation", msg)
            return False

        if frame.size == 0 or len(frame.shape) < 2:
            msg = f"Empty frame dimensions: {frame.shape}. Dropping frame."
            logger.warning(msg)
            context.add_error("validation", msg)
            return False

        return True

    def _stage_preprocess_frame(self, context: PipelineContext):
        """Stage 2: Frame Preprocessing placeholder (resizing/normalization)."""
        # Make a copy of the frame to draw overlays on, preserving raw_frame
        context.working_frame = context.raw_frame.copy()

    def _execute_module_safely(self, name: str, context: PipelineContext):
        """Execute a module. Catch and log errors without crashing the pipeline."""
        mod = module_registry.get(name)
        if mod is None:
            msg = f"Module '{name}' was enabled in config but not registered."
            logger.warning(msg)
            context.add_warning(name, msg)
            return

        try:
            results, errors, warnings = mod.process(context.raw_frame, context)
            
            # Merge results into metadata
            if results:
                context.metadata[name] = results
                
            # Append error/warning lists
            if errors:
                for err in errors:
                    context.add_error(name, err.get("message") if isinstance(err, dict) else str(err))
            if warnings:
                for warn in warnings:
                    context.add_warning(name, warn.get("message") if isinstance(warn, dict) else str(warn))
        except Exception as e:
            # Fatal error inside the module: catch it, log, and recover
            logger.exception(f"Exception raised in pipeline module '{name}': {e}")
            context.add_error(name, f"Unhandled exception: {e}")

    def _stage_visualize(self, context: PipelineContext):
        """Stage 7: Draw visualization overlays using placeholders."""
        # 1. Bounding Boxes Overlay placeholder
        if self.visualization_config.get("draw_boxes", True):
            self._draw_bounding_boxes_placeholder(context)

        # 2. Tracking IDs Overlay placeholder
        if self.visualization_config.get("draw_ids", True):
            self._draw_tracking_ids_placeholder(context)

        # 3. Violation Labels Overlay placeholder
        if self.visualization_config.get("draw_labels", True):
            self._draw_violation_labels_placeholder(context)

        # 4. Regions of Interest (ROI) Overlay placeholder
        if self.visualization_config.get("draw_roi", True):
            self._draw_roi_placeholder(context)

        # 5. Trails Overlay placeholder
        if self.visualization_config.get("draw_trails", False):
            self._draw_trails_placeholder(context)

        # 6. Heatmaps Overlay placeholder
        if self.visualization_config.get("draw_heatmap", False):
            self._draw_heatmap_placeholder(context)

    # --- Placeholders for overlays ---

    def _draw_bounding_boxes_placeholder(self, context: PipelineContext):
        """Placeholder for drawing bounding boxes."""
        # Note: Bounding boxes are actually drawn in Stage 3/4 via draw_tracked() in camera_manager
        # but we keep this visualizer hook for customization in future stages.
        if context.tracked_detections is not None:
            # Draw using inference service helper to maintain current rendering loop
            context.working_frame = inference_service.draw_tracked(
                context.working_frame, context.tracked_detections
            )
        elif context.raw_detections is not None:
            # Draw raw detections if tracking is off
            context.working_frame = inference_service.draw_tracked(
                context.working_frame, context.raw_detections
            )

    def _draw_tracking_ids_placeholder(self, context: PipelineContext):
        """Placeholder for drawing tracking IDs."""
        pass

    def _draw_violation_labels_placeholder(self, context: PipelineContext):
        """Placeholder for drawing violation labels."""
        pass

    def _draw_roi_placeholder(self, context: PipelineContext):
        """Placeholder for drawing Regions of Interest (ROI)."""
        pass

    def _draw_trails_placeholder(self, context: PipelineContext):
        """Placeholder for drawing vehicle history trails."""
        pass

    def _draw_heatmap_placeholder(self, context: PipelineContext):
        """Placeholder for drawing density heatmaps."""
        pass


# Global singleton
pipeline_manager = PipelineManager()
