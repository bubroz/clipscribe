"""Unit tests for gemini_pool.py module."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from clipscribe.retrievers.gemini_pool import GeminiPool, TaskType


@pytest.fixture
def gemini_pool():
    """Create a GeminiPool instance for testing."""
    return GeminiPool(model_name="gemini-2.5-flash", api_key="test_key")


class TestTaskType:
    """Test TaskType enum values."""

    def test_all_task_types_defined(self):
        """Test that all expected task types are defined."""
        expected_types = [
            "transcription",
            "key_points",
            "summary",
            "entities",
            "topics",
            "relationships",
            "entity_cleaning",
            "relationship_cleaning",
            "validation",
            "temporal_intelligence"
        ]

        for task_type in expected_types:
            assert hasattr(TaskType, task_type.upper())
            assert TaskType[task_type.upper()].value == task_type

    def test_task_type_values(self):
        """Test that task type values are correct."""
        assert TaskType.TRANSCRIPTION.value == "transcription"
        assert TaskType.KEY_POINTS.value == "key_points"
        assert TaskType.TEMPORAL_INTELLIGENCE.value == "temporal_intelligence"


class TestGeminiPoolInitialization:
    """Test GeminiPool initialization."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        pool = GeminiPool()

        assert pool.model_name == "gemini-2.5-flash"
        assert pool.api_key is None
        assert pool._models == {}

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        pool = GeminiPool(model_name="gemini-2.5-pro", api_key="custom_key")

        assert pool.model_name == "gemini-2.5-pro"
        assert pool.api_key == "custom_key"
        assert pool._models == {}

    @patch('clipscribe.retrievers.gemini_pool.genai.configure')
    def test_init_configures_api_key(self, mock_configure):
        """Test that API key is configured during initialization."""
        # Create a new instance to test the configuration
        GeminiPool(model_name="gemini-2.5-flash", api_key="test_key")
        mock_configure.assert_called_once_with(api_key="test_key")

    @patch('clipscribe.retrievers.gemini_pool.genai.configure')
    def test_init_no_api_key_uses_env_var(self, mock_configure):
        """Test that None API key uses environment variable."""
        pool = GeminiPool()

        # Should be called with api_key=None to use GOOGLE_API_KEY env var
        mock_configure.assert_called_once_with(api_key=None)


class TestGeminiPoolGetModel:
    """Test get_model functionality."""

    @patch('clipscribe.retrievers.gemini_pool.genai.GenerativeModel')
    def test_get_model_creates_new_instance(self, mock_model_class, gemini_pool):
        """Test that get_model creates a new instance for new task types."""
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance

        result = gemini_pool.get_model(TaskType.TRANSCRIPTION)

        assert result == mock_model_instance
        mock_model_class.assert_called_once_with("gemini-2.5-flash")
        assert TaskType.TRANSCRIPTION in gemini_pool._models

    @patch('clipscribe.retrievers.gemini_pool.genai.GenerativeModel')
    def test_get_model_reuses_existing_instance(self, mock_model_class, gemini_pool):
        """Test that get_model reuses existing instances."""
        mock_model_instance = MagicMock()
        gemini_pool._models[TaskType.TRANSCRIPTION] = mock_model_instance

        result = gemini_pool.get_model(TaskType.TRANSCRIPTION)

        assert result == mock_model_instance
        # Should not create a new instance
        mock_model_class.assert_not_called()

    @patch('clipscribe.retrievers.gemini_pool.genai.GenerativeModel')
    def test_get_model_different_task_types_create_separate_instances(self, mock_model_class, gemini_pool):
        """Test that different task types get separate instances."""
        mock_model_1 = MagicMock()
        mock_model_2 = MagicMock()
        mock_model_class.side_effect = [mock_model_1, mock_model_2]

        result1 = gemini_pool.get_model(TaskType.TRANSCRIPTION)
        result2 = gemini_pool.get_model(TaskType.SUMMARY)

        assert result1 == mock_model_1
        assert result2 == mock_model_2
        assert mock_model_class.call_count == 2
        assert len(gemini_pool._models) == 2


class TestGeminiPoolContextManagement:
    """Test context management functionality."""

    def test_clear_task_context_existing_task(self, gemini_pool):
        """Test clearing context for existing task."""
        mock_model = MagicMock()
        gemini_pool._models[TaskType.TRANSCRIPTION] = mock_model

        with patch('clipscribe.retrievers.gemini_pool.genai.GenerativeModel') as mock_model_class:
            new_mock_model = MagicMock()
            mock_model_class.return_value = new_mock_model

            gemini_pool.clear_task_context(TaskType.TRANSCRIPTION)

            assert gemini_pool._models[TaskType.TRANSCRIPTION] == new_mock_model
            mock_model_class.assert_called_once_with("gemini-2.5-flash")

    def test_clear_task_context_nonexistent_task(self, gemini_pool):
        """Test clearing context for non-existent task does nothing."""
        with patch('clipscribe.retrievers.gemini_pool.genai.GenerativeModel') as mock_model_class:
            gemini_pool.clear_task_context(TaskType.TRANSCRIPTION)

            # Should not create a new model instance
            mock_model_class.assert_not_called()

    def test_clear_all_contexts(self, gemini_pool):
        """Test clearing all contexts."""
        gemini_pool._models = {
            TaskType.TRANSCRIPTION: MagicMock(),
            TaskType.SUMMARY: MagicMock(),
            TaskType.ENTITIES: MagicMock()
        }

        gemini_pool.clear_all_contexts()

        assert gemini_pool._models == {}


class TestGeminiPoolGenerateForTask:
    """Test generate_for_task functionality."""

    @pytest.mark.asyncio
    async def test_generate_for_task_without_media_file(self, gemini_pool):
        """Test generating content without media file."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        gemini_pool._models[TaskType.TRANSCRIPTION] = mock_model

        result = await gemini_pool.generate_for_task(
            TaskType.TRANSCRIPTION,
            "Test prompt",
            timeout=300
        )

        assert result == mock_response
        mock_model.generate_content_async.assert_called_once()
        call_args = mock_model.generate_content_async.call_args
        assert call_args[0][0] == "Test prompt"  # content
        assert call_args[1]['request_options'].timeout == 300

    @pytest.mark.asyncio
    async def test_generate_for_task_with_media_file(self, gemini_pool):
        """Test generating content with media file."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        gemini_pool._models[TaskType.TRANSCRIPTION] = mock_model

        mock_media_file = MagicMock()

        result = await gemini_pool.generate_for_task(
            TaskType.TRANSCRIPTION,
            "Test prompt",
            media_file=mock_media_file,
            timeout=600
        )

        assert result == mock_response
        mock_model.generate_content_async.assert_called_once()
        call_args = mock_model.generate_content_async.call_args
        assert call_args[0][0] == [mock_media_file, "Test prompt"]  # content with media
        assert call_args[1]['request_options'].timeout == 600

    @pytest.mark.asyncio
    async def test_generate_for_task_with_additional_kwargs(self, gemini_pool):
        """Test generating content with additional kwargs."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        gemini_pool._models[TaskType.TRANSCRIPTION] = mock_model

        result = await gemini_pool.generate_for_task(
            TaskType.TRANSCRIPTION,
            "Test prompt",
            temperature=0.7,
            max_tokens=1000
        )

        assert result == mock_response
        call_args = mock_model.generate_content_async.call_args
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 1000

    @pytest.mark.asyncio
    async def test_generate_for_task_creates_model_if_not_exists(self, gemini_pool):
        """Test that generate_for_task creates model if it doesn't exist."""
        with patch('clipscribe.retrievers.gemini_pool.genai.GenerativeModel') as mock_model_class:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_model_class.return_value = mock_model

            result = await gemini_pool.generate_for_task(
                TaskType.TRANSCRIPTION,
                "Test prompt"
            )

            assert result == mock_response
            mock_model_class.assert_called_once_with("gemini-2.5-flash")


class TestGeminiPoolStats:
    """Test pool statistics functionality."""

    def test_get_pool_stats_empty_pool(self, gemini_pool):
        """Test getting stats for empty pool."""
        stats = gemini_pool.get_pool_stats()

        assert stats == {
            "active_models": 0,
            "task_types": []
        }

    def test_get_pool_stats_with_models(self, gemini_pool):
        """Test getting stats for pool with models."""
        gemini_pool._models = {
            TaskType.TRANSCRIPTION: MagicMock(),
            TaskType.SUMMARY: MagicMock(),
            TaskType.ENTITIES: MagicMock()
        }

        stats = gemini_pool.get_pool_stats()

        assert stats["active_models"] == 3
        assert set(stats["task_types"]) == {"transcription", "summary", "entities"}


class TestGeminiPoolErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_generate_for_task_with_timeout_error(self, gemini_pool):
        """Test handling of timeout errors."""
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("Request timeout"))

        gemini_pool._models[TaskType.TRANSCRIPTION] = mock_model

        with pytest.raises(Exception, match="Request timeout"):
            await gemini_pool.generate_for_task(
                TaskType.TRANSCRIPTION,
                "Test prompt",
                timeout=30
            )

    def test_get_model_with_invalid_task_type(self, gemini_pool):
        """Test that get_model works with all valid task types."""
        for task_type in TaskType:
            model = gemini_pool.get_model(task_type)
            assert model is not None
            assert task_type in gemini_pool._models
