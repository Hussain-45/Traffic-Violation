"""
Base AI Module Interface
=========================
Defines the required interface for all AI modules plugged into the pipeline.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import numpy as np
from ai.pipelines.pipeline_context import PipelineContext


class BaseAIModule(ABC):
    """
    Abstract Base Class for all AI modules in the pipeline.
    Any custom detection, tracking, or violation logic module must inherit from this class.
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the module.
        Load neural network weights, initialize configurations, or setup third-party services.
        """
        pass

    @abstractmethod
    def process(
        self, frame: np.ndarray, context: PipelineContext
    ) -> Tuple[Dict[str, Any], list, list]:
        """
        Execute the module's core logic on the given frame.

        Parameters
        ----------
        frame   : The current video frame as a NumPy array (BGR format).
        context : The shared PipelineContext object representing current frame processing state.

        Returns
        -------
        results  : A dictionary containing module-specific findings to merge into context.metadata.
        errors   : A list of non-fatal error dictionaries/messages generated during processing.
        warnings : A list of non-fatal warning dictionaries/messages generated during processing.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """
        Release loaded resources, unload models, or close files/connections.
        """
        pass

    @abstractmethod
    def health(self) -> bool:
        """
        Return True if the module is healthy and ready to process frames, False otherwise.
        """
        pass

    @abstractmethod
    def status(self) -> Dict[str, Any]:
        """
        Return a metadata dictionary with details about the module status (e.g. loaded model path, parameters, healthy status).
        """
        pass
