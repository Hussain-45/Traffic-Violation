import cv2
import yaml
import time
import threading
import numpy as np
from typing import Union, Tuple, Optional, Dict
from loguru import logger
from backend.app.services.inference_service import inference_service
from backend.app.services.tracking_service import tracking_service
from ai.pipelines.pipeline_manager import pipeline_manager


class CameraManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.config_path = "configs/camera.yaml"

        # Defaults
        self.default_source: Union[int, str] = 0
        self.target_fps: int = 30
        self.width: int = 1280
        self.height: int = 720
        self.max_reconnect_attempts: int = 5
        self.timeout: float = 5.0
        self.buffer_size: int = 2

        self.load_config()

        # Runtime state
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_source: Union[int, str] = self.default_source
        self.source_type: str = "Webcam"
        self.is_connected: bool = False

        self.running: bool = False
        self.capture_thread: Optional[threading.Thread] = None
        self.inference_thread: Optional[threading.Thread] = None

        # Diagnostics
        self.actual_fps: float = 0.0
        self.dropped_frames: int = 0
        self.reconnect_attempts: int = 0
        self.last_frame_timestamp: float = 0.0

        # Shared buffers
        self.latest_raw_frame: Optional[np.ndarray] = None
        self.latest_processed_jpeg: Optional[bytes] = None
        self.latest_counts: Dict[str, int] = {
            "total_vehicles": 0, "car": 0, "motorcycle": 0,
            "truck": 0, "bus": 0, "person": 0, "bicycle": 0
        }
        self.state_lock = threading.Lock()

        self.connect(self.default_source)

    # ------------------------------------------------------------------
    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
                self.default_source = cfg.get("default_camera", 0)
                self.target_fps = cfg.get("fps", 30)
                self.width = cfg.get("width", 1280)
                self.height = cfg.get("height", 720)
                self.max_reconnect_attempts = cfg.get("reconnect_attempts", 5)
                self.timeout = cfg.get("timeout", 5.0)
                self.buffer_size = cfg.get("buffer_size", 2)
                logger.info(f"Loaded camera config from {self.config_path}")
        except Exception as e:
            logger.warning(f"Failed to load camera config: {e}. Using defaults.")

    # ------------------------------------------------------------------
    def connect(self, source: Union[int, str]) -> Tuple[bool, str]:
        with self.state_lock:
            if self.running:
                self._disconnect_unsafe()

            self.current_source = source
            if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
                self.current_source = int(source)
                self.source_type = "Webcam"
            elif isinstance(source, str) and (source.startswith("rtsp://") or source.startswith("rtmp://")):
                self.source_type = "RTSP Camera"
            elif isinstance(source, str) and (source.startswith("http://") or source.startswith("https://")):
                self.source_type = "IP Camera"
            else:
                self.source_type = "Video File"

            logger.info(f"Connecting to {self.current_source} ({self.source_type})")
            self.cap = cv2.VideoCapture(self.current_source)
            if not self.cap.isOpened():
                self.is_connected = False
                self.cap.release()
                self.cap = None
                msg = f"Failed to open camera source: {self.current_source}"
                logger.error(msg)
                return False, msg

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

            self.is_connected = True
            self.running = True
            self.reconnect_attempts = 0
            self.dropped_frames = 0
            self.last_frame_timestamp = time.time()

            # Reset tracker state on new source
            tracking_service.reset()

            self.capture_thread = threading.Thread(
                target=self._capture_loop, daemon=True, name="CaptureThread"
            )
            self.inference_thread = threading.Thread(
                target=self._inference_loop, daemon=True, name="InferenceThread"
            )
            self.capture_thread.start()
            self.inference_thread.start()

            logger.info("Camera connected. Capture + Inference+Tracking threads started.")
            return True, "Connected successfully"

    def disconnect(self):
        with self.state_lock:
            self._disconnect_unsafe()

    def _disconnect_unsafe(self):
        self.running = False
        for t in (self.capture_thread, self.inference_thread):
            if t:
                t.join(timeout=1.0)
        self.capture_thread = None
        self.inference_thread = None
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_connected = False
        self.latest_raw_frame = None
        self.latest_processed_jpeg = None
        self.latest_counts = {
            "total_vehicles": 0, "car": 0, "motorcycle": 0,
            "truck": 0, "bus": 0, "person": 0, "bicycle": 0
        }
        logger.info(f"Camera {self.current_source} disconnected.")

    # ------------------------------------------------------------------
    def _capture_loop(self):
        frame_interval = 1.0 / self.target_fps
        last_time = time.time()
        fps_smooth = 0.9

        while self.running:
            t0 = time.time()
            if self.cap is None or not self.cap.isOpened():
                self._handle_reconnect()
                time.sleep(0.5)
                continue

            ret, frame = self.cap.read()
            if not ret:
                self.dropped_frames += 1
                if self.dropped_frames > self.max_reconnect_attempts:
                    self.is_connected = False
                    self._handle_reconnect()
                time.sleep(0.1)
                continue

            now = time.time()
            elapsed = now - last_time
            last_time = now
            if elapsed > 0:
                self.actual_fps = (
                    self.actual_fps * fps_smooth + (1.0 / elapsed) * (1.0 - fps_smooth)
                )

            self.last_frame_timestamp = now
            self.is_connected = True

            with self.state_lock:
                self.latest_raw_frame = frame

            sleep_time = frame_interval - (time.time() - t0)
            if sleep_time > 0:
                time.sleep(sleep_time)

    # ------------------------------------------------------------------
    def _inference_loop(self):
        """
        Processes each frame through the centralized PipelineManager.
        """
        last_ts = 0.0

        while self.running:
            if getattr(self, "paused", False):
                time.sleep(0.05)
                continue

            raw_frame = None
            ts = 0.0

            with self.state_lock:
                if (
                    self.latest_raw_frame is not None
                    and self.last_frame_timestamp > last_ts
                ):
                    raw_frame = self.latest_raw_frame.copy()
                    ts = self.last_frame_timestamp

            if raw_frame is None:
                time.sleep(0.01)
                continue

            # Process frame through PipelineManager
            result = pipeline_manager.process_frame(raw_frame, timestamp=ts)

            # Get visualized frame (fallback to raw_frame if visualization failed or is off)
            drawn = result.visualized_frame if result.visualized_frame is not None else raw_frame

            # Encode to JPEG
            ok, jpeg = cv2.imencode(".jpg", drawn)
            if ok:
                with self.state_lock:
                    self.latest_processed_jpeg = jpeg.tobytes()
                    self.latest_counts = result.counts

            last_ts = ts
            time.sleep(0.01)

    # ------------------------------------------------------------------
    def _handle_reconnect(self):
        logger.warning(f"Attempting reconnect to {self.current_source}…")
        if self.cap:
            self.cap.release()
            self.cap = None
        self.reconnect_attempts += 1
        if self.reconnect_attempts > self.max_reconnect_attempts:
            logger.error("Max reconnect attempts exceeded. Giving up.")
            self.is_connected = False
            return
        self.cap = cv2.VideoCapture(self.current_source)
        if self.cap.isOpened():
            logger.info("Camera reconnected.")
            self.is_connected = True
            self.dropped_frames = 0
            self.reconnect_attempts = 0

    # ------------------------------------------------------------------
    def get_frame(self) -> Tuple[Optional[bytes], str]:
        """Returns latest annotated JPEG; falls back to simulated pattern."""
        with self.state_lock:
            if self.is_connected and self.latest_processed_jpeg:
                return self.latest_processed_jpeg, self.source_type

        # --- Simulated offline pattern ---
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for i in range(0, self.width, 100):
            cv2.line(frame, (i, 0), (i, self.height), (22, 27, 36), 1)
        for j in range(0, self.height, 100):
            cv2.line(frame, (0, j), (self.width, j), (22, 27, 36), 1)
        cx, cy = self.width // 2, self.height // 2
        for r in range(50, 300, 50):
            cv2.circle(frame, (cx, cy), r, (31, 41, 61), 2)
        bx = int(cx + 100 * np.sin(time.time() * 2))
        by = int(cy + 50 * np.cos(time.time() * 2))
        cv2.rectangle(frame, (bx - 30, by - 30), (bx + 30, by + 30), (6, 182, 212), -1)
        cv2.putText(frame, "TRAFFIC VIOLATION AI", (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "CAMERA OFFLINE — SIMULATED", (50, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (239, 68, 68), 2)
        ok, jpeg = cv2.imencode(".jpg", frame)
        return (jpeg.tobytes() if ok else None), "Simulated"


# Global singleton
camera_manager = CameraManager()
