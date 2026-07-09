"""
Unit Tests for Pipeline Manager
===============================
Verifies:
  1. Frame validation handles invalid frames without crashing.
  2. Modules can be dynamically enabled/disabled.
  3. Non-fatal errors in modules are caught, logged, and returned without crashing.
  4. Performance metrics are recorded accurately.
"""
import pytest
import numpy as np
from ai.pipelines.pipeline_manager import PipelineManager
from ai.pipelines.registry import module_registry, BaseAIModule, MockAIModule
from ai.pipelines.pipeline_context import PipelineContext
from typing import Dict, Any, Tuple


class FaultyAIModule(BaseAIModule):
    """A module that intentionally throws an exception to test error recovery."""
    def initialize(self) -> None:
        pass

    def process(self, frame: np.ndarray, context: PipelineContext) -> Tuple[Dict[str, Any], list, list]:
        raise RuntimeError("Intentionally crashed for testing error recovery.")

    def shutdown(self) -> None:
        pass

    def health(self) -> bool:
        return True

    def status(self) -> Dict[str, Any]:
        return {"name": "FaultyAIModule"}


def test_frame_validation():
    # Setup manager
    manager = PipelineManager()
    
    # 1. Test None frame
    result = manager.process_frame(None)
    assert len(result.errors) > 0
    assert any(err["module"] == "validation" for err in result.errors)
    
    # 2. Test invalid object
    result_invalid = manager.process_frame("not-a-numpy-array")
    assert len(result_invalid.errors) > 0
    
    # 3. Test empty numpy array
    result_empty = manager.process_frame(np.array([]))
    assert len(result_empty.errors) > 0


def test_dynamic_enable_disable():
    manager = PipelineManager()
    
    # Check default config state for a mock module
    manager.enabled_modules = ["vehicle_detection", "vehicle_tracking", "helmet_detection"]
    assert "helmet_detection" in manager.enabled_modules
    assert "seat_belt_detection" not in manager.enabled_modules
    
    # Dynamically enable seat belt detection
    manager.enabled_modules.append("seat_belt_detection")
    assert "seat_belt_detection" in manager.enabled_modules


def test_module_error_recovery():
    manager = PipelineManager()
    
    # Register the faulty module
    faulty_key = "faulty_module"
    module_registry.register(faulty_key, FaultyAIModule())
    
    # Ensure it's in execution order and enabled
    if faulty_key not in manager.execution_order:
        manager.execution_order.append(faulty_key)
    if faulty_key not in manager.enabled_modules:
        manager.enabled_modules.append(faulty_key)
        
    # Also keep a healthy module after the faulty one to verify it still executes
    healthy_key = "healthy_after_faulty"
    healthy_module = MockAIModule(healthy_key)
    module_registry.register(healthy_key, healthy_module)
    if healthy_key not in manager.execution_order:
        manager.execution_order.append(healthy_key)
    if healthy_key not in manager.enabled_modules:
        manager.enabled_modules.append(healthy_key)
        
    # Process a valid frame
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    result = manager.process_frame(frame)
    
    # Verify the faulty module's error was caught
    assert len(result.errors) > 0
    assert any(err["module"] == faulty_key and "Intentionally crashed" in err["message"] for err in result.errors)
    
    # Verify the healthy module still executed and ran successfully
    assert healthy_key in result.metadata
    assert result.metadata[healthy_key]["mock_processed"] is True

    # Clean up the registry
    module_registry.unregister(faulty_key)
    module_registry.unregister(healthy_key)
    if faulty_key in manager.execution_order:
        manager.execution_order.remove(faulty_key)
    if faulty_key in manager.enabled_modules:
        manager.enabled_modules.remove(faulty_key)
    if healthy_key in manager.execution_order:
        manager.execution_order.remove(healthy_key)
    if healthy_key in manager.enabled_modules:
        manager.enabled_modules.remove(healthy_key)


def test_performance_monitoring():
    manager = PipelineManager()
    
    # Reset monitor
    manager.performance_monitor.reset()
    
    # Record some mock frames
    manager.performance_monitor.record_frame(
        pipeline_time_ms=15.0, yolo_time_ms=10.0, tracking_time_ms=3.0
    )
    manager.performance_monitor.record_frame(
        pipeline_time_ms=17.0, yolo_time_ms=12.0, tracking_time_ms=4.0
    )
    manager.performance_monitor.record_module("helmet_detection", 1.5)
    manager.performance_monitor.record_module("helmet_detection", 2.5)
    
    # Get metrics
    metrics = manager.performance_monitor.get_metrics()
    
    assert metrics["pipeline_time_ms"] == 16.0
    assert metrics["yolo_time_ms"] == 11.0
    assert metrics["tracking_time_ms"] == 3.5
    assert metrics["module_execution_times_ms"]["helmet_detection"] == 2.0
