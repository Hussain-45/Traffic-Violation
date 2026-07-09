"""
Performance Monitor
===================
Tracks processing times for various stages of the AI pipeline,
calculates running averages, and computes real-time FPS metrics.
"""
import time
import threading
from collections import deque
from typing import Dict, Any, List


class PerformanceMonitor:
    """
    Thread-safe performance monitoring class for the AI pipeline.
    Tracks frame processing time, pipeline steps, module execution times, and average FPS.
    """

    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self._lock = threading.RLock()

        # Sliding window history of step durations (in milliseconds)
        self.total_pipeline_times = deque(maxlen=history_size)
        self.yolo_times = deque(maxlen=history_size)
        self.tracking_times = deque(maxlen=history_size)
        
        # Module-specific execution times history: { module_name: deque }
        self.module_times: Dict[str, deque] = {}

        # Tracking frame count for FPS calculation
        self.fps_timestamps = deque(maxlen=history_size)

        # Queue size (can be set by camera/pipeline queues)
        self.current_queue_size = 0

    def record_frame(self, pipeline_time_ms: float, yolo_time_ms: float, tracking_time_ms: float):
        """Record base pipeline execution metrics for a single frame."""
        with self._lock:
            self.total_pipeline_times.append(pipeline_time_ms)
            self.yolo_times.append(yolo_time_ms)
            self.tracking_times.append(tracking_time_ms)
            self.fps_timestamps.append(time.time())

    def record_module(self, module_name: str, duration_ms: float):
        """Record custom AI module execution duration."""
        with self._lock:
            if module_name not in self.module_times:
                self.module_times[module_name] = deque(maxlen=self.history_size)
            self.module_times[module_name].append(duration_ms)

    def set_queue_size(self, size: int):
        """Set the current queue size."""
        with self._lock:
            self.current_queue_size = max(0, size)

    def get_average_fps(self) -> float:
        """Calculate average FPS based on the timestamps of processed frames."""
        with self._lock:
            if len(self.fps_timestamps) < 2:
                return 0.0
            total_duration = self.fps_timestamps[-1] - self.fps_timestamps[0]
            if total_duration <= 0:
                return 0.0
            return (len(self.fps_timestamps) - 1) / total_duration

    def get_metrics(self) -> Dict[str, Any]:
        """Compile and return all tracked performance metrics."""
        with self._lock:
            def get_avg(dq: deque) -> float:
                return round(sum(dq) / len(dq), 2) if len(dq) > 0 else 0.0

            module_averages = {
                name: get_avg(dq) for name, dq in self.module_times.items()
            }

            avg_fps = self.get_average_fps()

            return {
                "pipeline_time_ms": get_avg(self.total_pipeline_times),
                "yolo_time_ms": get_avg(self.yolo_times),
                "tracking_time_ms": get_avg(self.tracking_times),
                "average_fps": round(avg_fps, 2),
                "queue_size": self.current_queue_size,
                "module_execution_times_ms": module_averages,
            }

    def reset(self):
        """Reset all metric histories."""
        with self._lock:
            self.total_pipeline_times.clear()
            self.yolo_times.clear()
            self.tracking_times.clear()
            self.module_times.clear()
            self.fps_timestamps.clear()
            self.current_queue_size = 0
