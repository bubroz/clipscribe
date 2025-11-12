"""
DEPRECATED: Legacy Gemini transcriber classes.

These classes have been replaced by the Voxtral-Grok pipeline in VideoIntelligenceRetrieverV2.
This file exists only to prevent import errors in legacy tests.
"""

import logging
import warnings
from typing import Any, Dict

logger = logging.getLogger(__name__)


class GeminiFlashTranscriber:
    """
    DEPRECATED: Mock class to prevent import errors.

    Original functionality moved to HybridProcessor in VideoIntelligenceRetrieverV2.
    """

    def __init__(self, use_pro: bool = False, use_vertex_ai: bool = False):
        warnings.warn(
            "GeminiFlashTranscriber is deprecated. Use VideoIntelligenceRetrieverV2 instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.warning("GeminiFlashTranscriber instantiated - this class is deprecated")

        self.use_pro = use_pro
        self.use_vertex_ai = use_vertex_ai
        self.model_name = "deprecated-gemini-flash"

    async def transcribe_audio(self, audio_path: str, duration: int) -> Dict[str, Any]:
        """Mock transcription method."""
        warnings.warn("transcribe_audio is deprecated", DeprecationWarning, stacklevel=2)
        return {
            "transcript": "DEPRECATED: Use Voxtral-Grok pipeline instead",
            "entities": [],
            "relationships": [],
            "model_used": "deprecated",
        }


class GeminiPool:
    """
    DEPRECATED: Mock class to prevent import errors.

    Original functionality moved to HybridProcessor.
    """

    def __init__(self):
        warnings.warn("GeminiPool is deprecated.", DeprecationWarning, stacklevel=2)
        logger.warning("GeminiPool instantiated - this class is deprecated")


class TaskType:
    """Mock enum for compatibility."""

    TRANSCRIBE = "transcribe"
    EXTRACT = "extract"
