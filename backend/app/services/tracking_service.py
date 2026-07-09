"""
Tracking Service — ByteTrack integration.

Wraps supervision.ByteTrack to assign persistent IDs to detected vehicles
across frames. Separation from InferenceService allows the tracker to
maintain its internal state independently of detection.
"""
import time
import warnings
import numpy as np
import supervision as sv
from typing import Tuple, Dict, Set
from loguru import logger


# Suppress the v0.28 deprecation warning — ByteTrack still works in 0.29.x
warnings.filterwarnings("ignore", category=FutureWarning, module="supervision")


class TrackingService:
    """
    Singleton that wraps ByteTrack for multi-object vehicle tracking.

    Lifecycle:
        1. Instantiated once at module import.
        2. `update()` called each inference cycle with raw sv.Detections.
        3. Returns sv.Detections enriched with tracker_id.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        minimum_matching_threshold: float = 0.8,
        frame_rate: int = 30,
    ):
        if self._initialized:
            return
        self._initialized = True

        logger.info("Initializing ByteTrack tracker…")
        try:
            self.tracker = sv.ByteTrack(
                track_activation_threshold=track_activation_threshold,
                lost_track_buffer=lost_track_buffer,
                minimum_matching_threshold=minimum_matching_threshold,
                frame_rate=frame_rate,
            )
            logger.info("ByteTrack tracker initialized successfully.")
        except Exception as e:
            logger.critical(f"ByteTrack initialization failed: {e}")
            self.tracker = None
            raise

        # --- Statistics ---
        self.unique_ids: Set[int] = set()
        self.active_track_count: int = 0
        self.lost_track_count: int = 0
        self.tracking_fps: float = 0.0
        self._last_ts: float = 0.0
        self._fps_alpha: float = 0.9          # exponential moving average

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, detections: sv.Detections) -> sv.Detections:
        """
        Feed a frame's detections into ByteTrack and return tracked
        detections that carry a `tracker_id` for each object.

        Args:
            detections: sv.Detections with xyxy, confidence, class_id.

        Returns:
            sv.Detections enriched with tracker_id (or original detections
            on tracker failure).
        """
        if self.tracker is None:
            return detections

        t0 = time.perf_counter()

        try:
            tracked: sv.Detections = self.tracker.update_with_detections(detections)

            # --- Update statistics ---
            ids = set(tracked.tracker_id.tolist()) if tracked.tracker_id is not None else set()
            self.unique_ids.update(ids)
            self.active_track_count = len(ids)

            # Lost = IDs we have seen before that are not in this frame
            known = self.unique_ids
            self.lost_track_count = max(0, len(known) - self.active_track_count)

        except Exception as e:
            logger.error(f"ByteTrack update error: {e}")
            tracked = detections

        # FPS exponential moving average
        elapsed = time.perf_counter() - t0
        if elapsed > 0:
            inst_fps = 1.0 / elapsed
            self.tracking_fps = (
                self.tracking_fps * self._fps_alpha + inst_fps * (1.0 - self._fps_alpha)
            )

        return tracked

    def get_stats(self) -> Dict:
        return {
            "active_tracks": self.active_track_count,
            "unique_ids_seen": len(self.unique_ids),
            "lost_tracks": self.lost_track_count,
            "tracking_fps": round(self.tracking_fps, 2),
        }

    def reset(self):
        """Reset tracker state (e.g. on camera source change)."""
        if self.tracker:
            self.tracker.reset()
        self.unique_ids.clear()
        self.active_track_count = 0
        self.lost_track_count = 0
        self.tracking_fps = 0.0
        logger.info("ByteTrack tracker state reset.")


# Global singleton
tracking_service = TrackingService()
