"""
Pipeline Context
================
The shared data carrier that flows through every stage of the pipeline.
Every AI module receives a reference to the same context object and
appends its results without overwriting previous stages.
"""
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
import supervision as sv


@dataclass
class PipelineContext:
    """
    Single-frame context object passed through all pipeline stages.

    Attributes
    ----------
    frame_id        : Monotonically increasing frame counter.
    timestamp       : UNIX timestamp of when the frame was captured.
    raw_frame       : Original BGR frame from the camera (never modified).
    working_frame   : Mutable copy used for drawing overlays.
    raw_detections  : sv.Detections from YOLO (no tracker_id yet).
    tracked_detections : sv.Detections enriched with tracker_id by ByteTrack.
    config          : Snapshot of the pipeline config at processing time.
    metadata        : Arbitrary key-value pairs for inter-module communication.
    performance     : Timing data populated by PerformanceMonitor.
    errors          : Non-fatal errors collected during processing.
    warnings        : Non-fatal warnings collected during processing.
    detection_counts: Per-class counts for the current frame.
    """

    # --- Identity ---
    frame_id: int = 0
    timestamp: float = field(default_factory=time.time)

    # --- Frame data ---
    raw_frame: Optional[np.ndarray] = None
    working_frame: Optional[np.ndarray] = None

    # --- AI results ---
    raw_detections: Optional[sv.Detections] = None
    tracked_detections: Optional[sv.Detections] = None

    # --- Pipeline config (read-only copy) ---
    config: Dict[str, Any] = field(default_factory=dict)

    # --- Shared metadata (modules may write here) ---
    metadata: Dict[str, Any] = field(default_factory=dict)

    # --- Performance timing (populated by PerformanceMonitor) ---
    performance: Dict[str, float] = field(default_factory=dict)

    # --- Error / warning accumulation ---
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    # --- Detection statistics ---
    detection_counts: Dict[str, int] = field(default_factory=lambda: {
        "total_vehicles": 0,
        "car": 0, "motorcycle": 0, "truck": 0,
        "bus": 0, "bicycle": 0, "person": 0,
    })

    def is_valid(self) -> bool:
        """Return True if the context carries a usable frame."""
        return (
            self.raw_frame is not None
            and isinstance(self.raw_frame, np.ndarray)
            and self.raw_frame.size > 0
        )

    def add_error(self, module: str, message: str):
        self.errors.append({"module": module, "message": message, "ts": time.time()})

    def add_warning(self, module: str, message: str):
        self.warnings.append({"module": module, "message": message, "ts": time.time()})
