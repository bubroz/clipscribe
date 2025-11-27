"""
DEPRECATED: Legacy Gemini pool classes.

These classes have been replaced by the Voxtral-Grok pipeline.
This file exists only to prevent import errors in legacy tests.
"""

import logging
import warnings
from enum import Enum
from typing import Any, Dict

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Mock enum for compatibility."""

    TRANSCRIBE = "transcribe"
    EXTRACT = "extract"


class GeminiPool:
    """
    DEPRECATED: Mock class to prevent import errors.

    Original functionality moved to HybridProcessor.
    """

    def __init__(self):
        warnings.warn("GeminiPool is deprecated.", DeprecationWarning, stacklevel=2)
        logger.warning("GeminiPool instantiated - this class is deprecated")

    async def process_task(self, task_type: TaskType, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock processing method."""
        warnings.warn("process_task is deprecated", DeprecationWarning, stacklevel=2)
        return {
            "result": "DEPRECATED: Use Voxtral-Grok pipeline instead",
            "task_type": task_type.value,
        }
