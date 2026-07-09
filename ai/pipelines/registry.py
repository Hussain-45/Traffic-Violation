"""
AI Module Registry
==================
Contains the dynamic registry for all AI pipeline modules.
Also contains the actual pipeline wrappers for:
  - Vehicle Detection (using InferenceService)
  - Vehicle Tracking (using TrackingService)
and mock modules for the other pipeline keys.
"""
from typing import Dict, Any, Tuple, Optional
import numpy as np
import supervision as sv
from loguru import logger

from ai.pipelines.base_module import BaseAIModule
from ai.pipelines.pipeline_context import PipelineContext
from backend.app.services.inference_service import inference_service
from backend.app.services.tracking_service import tracking_service
from ai.detection.helmet_detection import HelmetDetectionModule
from ai.detection.seatbelt_detection import SeatBeltDetectionModule


class VehicleDetectionModule(BaseAIModule):
    """Wraps the InferenceService detect_raw() call."""

    def __init__(self):
        self._initialized = False

    def initialize(self) -> None:
        # InferenceService singleton loads the model on construction,
        # but we check if it is active.
        if inference_service.model is None:
            inference_service._load_model()
        self._initialized = True
        logger.info("VehicleDetectionModule initialized.")

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], list, list]:
        errors = []
        warnings = []
        results = {}

        try:
            detections, counts = inference_service.detect_raw(frame)
            context.raw_detections = detections
            context.detection_counts = counts
            results["counts"] = counts
        except Exception as e:
            logger.error(f"VehicleDetectionModule error: {e}")
            errors.append({"module": "vehicle_detection", "message": str(e)})

        return results, errors, warnings

    def shutdown(self) -> None:
        self._initialized = False
        logger.info("VehicleDetectionModule shut down.")

    def health(self) -> bool:
        return self._initialized and inference_service.model is not None

    def status(self) -> Dict[str, Any]:
        return {
            "name": "VehicleDetectionModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "model_path": inference_service.model_path if inference_service.model else "None",
        }


class VehicleTrackingModule(BaseAIModule):
    """Wraps the TrackingService update() call."""

    def __init__(self):
        self._initialized = False

    def initialize(self) -> None:
        # tracking_service resets or initializes ByteTrack
        tracking_service.reset()
        self._initialized = True
        logger.info("VehicleTrackingModule initialized.")

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], list, list]:
        errors = []
        warnings = []
        results = {}

        if context.raw_detections is None:
            warnings.append({
                "module": "vehicle_tracking",
                "message": "Raw detections are missing in context. Skipping tracking.",
            })
            return results, errors, warnings

        try:
            tracked = tracking_service.update(context.raw_detections)
            context.tracked_detections = tracked
            results["active_tracks"] = tracking_service.get_stats()["active_tracks"]
        except Exception as e:
            logger.error(f"VehicleTrackingModule error: {e}")
            errors.append({"module": "vehicle_tracking", "message": str(e)})

        return results, errors, warnings

    def shutdown(self) -> None:
        self._initialized = False
        logger.info("VehicleTrackingModule shut down.")

    def health(self) -> bool:
        return self._initialized

    def status(self) -> Dict[str, Any]:
        return {
            "name": "VehicleTrackingModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "stats": tracking_service.get_stats(),
        }


class MockAIModule(BaseAIModule):
    """General mock placeholder module for required interface logic without actual implementations."""

    def __init__(self, name: str):
        self.name = name
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True
        logger.info(f"MockAIModule '{self.name}' initialized.")

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], list, list]:
        # Return empty mock results and zero errors
        return {"mock_processed": True}, [], []

    def shutdown(self) -> None:
        self._initialized = False
        logger.info(f"MockAIModule '{self.name}' shut down.")

    def health(self) -> bool:
        return self._initialized

    def status(self) -> Dict[str, Any]:
        return {
            "name": f"MockAIModule({self.name})",
            "initialized": self._initialized,
            "healthy": self.health(),
        }


class AIModuleRegistry:
    """Dynamic registry managing all AI modules."""

    def __init__(self):
        self._registry: Dict[str, BaseAIModule] = {}
        self._register_default_modules()

    def _register_default_modules(self):
        # Register default pipeline modules
        self.register("vehicle_detection", VehicleDetectionModule())
        self.register("vehicle_tracking", VehicleTrackingModule())
        self.register("helmet_detection", HelmetDetectionModule())
        self.register("seat_belt_detection", SeatBeltDetectionModule())
        self.register("phone_detection", MockAIModule("phone_detection"))
        self.register("traffic_signal_detection", MockAIModule("traffic_signal_detection"))
        self.register("wrong_side_detection", MockAIModule("wrong_side_detection"))
        self.register("number_plate_detection", MockAIModule("number_plate_detection"))
        self.register("ocr", MockAIModule("ocr"))
        self.register("violation_engine", MockAIModule("violation_engine"))

    def register(self, key: str, module: BaseAIModule):
        """Add or overwrite a module in the registry."""
        if not isinstance(module, BaseAIModule):
            raise TypeError("Module must inherit from BaseAIModule")
        self._registry[key] = module
        logger.info(f"Registered module: '{key}'")

    def unregister(self, key: str):
        """Remove a module from the registry."""
        if key in self._registry:
            try:
                self._registry[key].shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down module '{key}' during unregistration: {e}")
            del self._registry[key]
            logger.info(f"Unregistered module: '{key}'")

    def get(self, key: str) -> Optional[BaseAIModule]:
        """Retrieve a module instance by its key."""
        return self._registry.get(key)

    def list_modules(self) -> Dict[str, Dict[str, Any]]:
        """List status of all registered modules."""
        return {key: mod.status() for key, mod in self._registry.items()}

    def initialize_all(self):
        """Initialize all registered modules."""
        for key, mod in self._registry.items():
            try:
                mod.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize module '{key}': {e}")

    def shutdown_all(self):
        """Shut down all registered modules."""
        for key, mod in self._registry.items():
            try:
                mod.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down module '{key}': {e}")


# Global registry singleton
module_registry = AIModuleRegistry()
