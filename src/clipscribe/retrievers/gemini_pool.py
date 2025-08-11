"""
Gemini Model Pool - Manage multiple Gemini instances for different tasks.

This avoids token limit issues by using fresh instances for each task type 
"""

import logging
from typing import Dict, Optional
from enum import Enum
import google.generativeai as genai
from google.generativeai.types import RequestOptions

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Different task types that need separate Gemini instances."""

    TRANSCRIPTION = "transcription"
    KEY_POINTS = "key_points"
    SUMMARY = "summary"
    ENTITIES = "entities"
    TOPICS = "topics"
    RELATIONSHIPS = "relationships"
    ENTITY_CLEANING = "entity_cleaning"
    RELATIONSHIP_CLEANING = "relationship_cleaning"
    VALIDATION = "validation"
    # v2.17.0 Enhanced Temporal Intelligence
    TEMPORAL_INTELLIGENCE = "temporal_intelligence"


class GeminiPool:
    """
    Manage a pool of Gemini model instances.

    Each task gets its own instance to avoid context pollution and token limits.
    This is like having multiple AI assistants, each specialized for one job
    """

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        """Initialize the Gemini pool."""
        self.model_name = model_name
        self.api_key = api_key
        self._models: Dict[TaskType, genai.GenerativeModel] = {}

        # Configure API key once
        if api_key:
            genai.configure(api_key=api_key)
        else:
            genai.configure(api_key=None)  # Uses GOOGLE_API_KEY env var

    def get_model(self, task_type: TaskType) -> genai.GenerativeModel:
        """
        Get a Gemini model instance for a specific task.

        Creates a new instance if one doesn't exist for this task.
        Each task gets its own clean instance without previous context.
        """
        if task_type not in self._models:
            logger.info(f"Creating new Gemini instance for {task_type.value}")
            self._models[task_type] = genai.GenerativeModel(self.model_name)

        return self._models[task_type]

    def clear_task_context(self, task_type: TaskType):
        """
        Clear the context for a specific task by creating a new instance.

        Useful when processing multiple videos to avoid context buildup.
        """
        if task_type in self._models:
            logger.info(f"Clearing context for {task_type.value}")
            # Create a fresh instance
            self._models[task_type] = genai.GenerativeModel(self.model_name)

    def clear_all_contexts(self):
        """Clear all model contexts by recreating all instances."""
        logger.info("Clearing all Gemini contexts")
        self._models.clear()

    async def generate_for_task(
        self, task_type: TaskType, prompt: str, media_file=None, timeout: int = 600, **kwargs
    ):
        """
        Generate content for a specific task using its dedicated model.

        Args:
            task_type: The type of task
            prompt: The prompt to send
            media_file: Optional media file (for transcription)
            timeout: Request timeout in seconds
            **kwargs: Additional generation config

        Returns:
            Generated response
        """
        model = self.get_model(task_type)

        # Build the content
        if media_file:
            content = [media_file, prompt]
        else:
            content = prompt

        # Generate with timeout
        response = await model.generate_content_async(
            content, request_options=RequestOptions(timeout=timeout), **kwargs
        )

        return response

    def get_pool_stats(self) -> Dict[str, int]:
        """Get statistics about the model pool."""
        return {
            "active_models": len(self._models),
            "task_types": [task.value for task in self._models.keys()],
        }
