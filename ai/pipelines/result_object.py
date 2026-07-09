"""
Pipeline Result
===============
Defines the unified result structure returned by the PipelineManager.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import numpy as np
import supervision as sv


@dataclass
class PipelineResult:
    """
    Standardized AI pipeline result containing the output of a single frame execution.
    Allows downstream clients and modules to easily read predictions, diagnostics, and metrics.
    """
    # Monotonically increasing frame counter from camera capture
    frame_id: int

    # Captured timestamp
    timestamp: float

    # Original frame NumPy array (BGR)
    raw_frame: Optional[np.ndarray] = None

    # Visual result with visualization overlays drawn (BGR)
    visualized_frame: Optional[np.ndarray] = None

    # YOLO bounding boxes and predictions without track IDs
    detections: Optional[sv.Detections] = None

    # Detections enriched with tracking IDs from ByteTrack
    tracks: Optional[sv.Detections] = None

    # Execution timing metrics for uvicorn/frontend diagnostic integration
    timing: Dict[str, float] = field(default_factory=dict)

    # Collection of non-fatal errors during module execution
    errors: List[Dict[str, Any]] = field(default_factory=list)

    # Collection of warnings during module execution
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    # Combined output data from all modules (e.g. OCR text, Violation class, wrong-side flag)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Aggregated class counts (e.g. car: 3, motorcycle: 1, person: 0)
    counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result metadata and timings (excluding raw frame matrices) to a dictionary."""
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "timing": self.timing,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "counts": self.counts,
            "detections_count": len(self.detections) if self.detections is not None else 0,
            "tracks_count": len(self.tracks) if self.tracks is not None else 0,
        }
