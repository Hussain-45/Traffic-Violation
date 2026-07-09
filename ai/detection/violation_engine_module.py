"""
Violation Engine Pipeline Wrapper Module
========================================
Wrapper module inheriting from BaseAIModule to integrate ViolationDecisionEngine
into the centralized AI Pipeline Manager.
"""
from typing import Dict, Any, List, Tuple
import numpy as np
from loguru import logger

from ai.pipelines.base_module import BaseAIModule
from ai.pipelines.pipeline_context import PipelineContext
from ai.violations.violation_decision_engine import ViolationDecisionEngine


class ViolationEngineModule(BaseAIModule):
    """
    Pipeline wrapper for the business decision logic ViolationDecisionEngine.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.engine = ViolationDecisionEngine(pipeline_config_path=pipeline_config_path)
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self.engine.initialize()
        self._initialized = True
        logger.info("ViolationEngineModule wrapper initialized.")

    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], list, list]:
        errors = []
        warnings = []
        results = {
            "status": "Inactive",
            "records": []
        }

        if not self._initialized:
            warnings.append({"module": "violation_engine", "message": "Module not initialized."})
            return results, errors, warnings

        results["status"] = "Active"

        try:
            # Evaluate all active contexts and collect violation records
            records = self.engine.evaluate_all_active()
            results["records"] = [rec.to_dict() for rec in records]
            
            # Store directly in context metadata
            context.metadata["violation_engine"] = results
            
        except Exception as e:
            logger.exception(f"ViolationEngineModule execution error: {e}")
            errors.append({"module": "violation_engine", "message": str(e)})

        return results, errors, warnings

    def shutdown(self) -> None:
        self.engine.reset()
        self._initialized = False
        logger.info("ViolationEngineModule wrapper shut down.")

    def health(self) -> bool:
        return self._initialized

    def status(self) -> Dict[str, Any]:
        return {
            "name": "ViolationEngineModule",
            "initialized": self._initialized,
            "healthy": self.health(),
            "config": self.engine.config
        }
