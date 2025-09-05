"""
Comprehensive tests for the Unified Transcriber API.

Tests the complete API abstraction layer functionality including:
- Parameter mapping across backends
- Method resolution
- Error handling
- Backend switching
- Metrics collection
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from src.clipscribe.api.unified_transcriber import (
    UnifiedTranscriberAPI,
    BackendType,
    BackendRegistry,
    ParameterMapper,
    MethodResolver,
    UnifiedErrorHandler,
    MetricsCollector
)


class TestParameterMapper:
    """Test parameter mapping functionality."""

    def setup_method(self):
        self.mapper = ParameterMapper()

    def test_gemini_parameter_mapping(self):
        """Test parameter mapping for Gemini backend."""
        params = {
            "audio_path": "/test/audio.mp3",
            "duration": 120,
            "metadata": {"title": "test"}
        }

        mapped = self.mapper.map_parameters(BackendType.GEMINI, params)

        assert mapped["file_path"] == "/test/audio.mp3"
        assert mapped["duration_seconds"] == 120
        assert mapped["metadata"] == {"title": "test"}

    def test_vertex_parameter_mapping(self):
        """Test parameter mapping for Vertex backend."""
        params = {
            "file_path": "/test/video.mp4",
            "duration": 300,
            "language": "en"
        }

        mapped = self.mapper.map_parameters(BackendType.VERTEX, params)

        assert mapped["gcs_uri"] == "/test/video.mp4"
        assert mapped["duration"] == 300
        assert mapped["language"] == "en"

    def test_unknown_backend_mapping(self):
        """Test parameter mapping for unknown backend."""
        params = {"test": "value"}

        mapped = self.mapper.map_parameters(BackendType.GEMINI, params)

        # Should pass through unchanged
        assert mapped["test"] == "value"

    def test_path_validation(self):
        """Test path parameter validation."""
        # Valid path
        result = self.mapper._validate_path("/test/path.mp3")
        assert result == "/test/path.mp3"

        # Path object
        result = self.mapper._validate_path(Path("/test/path.mp3"))
        assert result == "/test/path.mp3"

        # Invalid path type
        with pytest.raises(ValueError):
            self.mapper._validate_path(123)


class TestMethodResolver:
    """Test method resolution functionality."""

    def setup_method(self):
        self.resolver = MethodResolver()

    def test_method_resolution_priority(self):
        """Test method resolution follows priority order."""
        mock_backend = Mock()

        # Add methods in reverse priority order
        mock_backend.extract = Mock()
        mock_backend.analyze = Mock()
        mock_backend.transcribe = Mock()

        method = self.resolver.resolve_method(mock_backend, "transcribe")

        assert method == mock_backend.transcribe

    def test_method_resolution_fallback(self):
        """Test method resolution falls back when primary method missing."""
        mock_backend = Mock()
        mock_backend.process = Mock()

        # Remove higher priority methods
        for method_name in ['transcribe', 'transcribe_audio', 'transcribe_video']:
            if hasattr(mock_backend, method_name):
                delattr(mock_backend, method_name)

        method = self.resolver.resolve_method(mock_backend, "transcribe")

        assert method == mock_backend.process

    def test_method_resolution_none(self):
        """Test method resolution returns None when no compatible method."""
        mock_backend = Mock()
        # Remove all methods from priority list
        for method_name in self.resolver.method_priority:
            if hasattr(mock_backend, method_name):
                delattr(mock_backend, method_name)

        method = self.resolver.resolve_method(mock_backend, "transcribe")

        assert method is None

    def test_async_method_compatibility(self):
        """Test async method compatibility detection."""
        mock_backend = Mock()
        mock_backend.transcribe = AsyncMock()

        is_compatible = self.resolver._is_compatible_method(mock_backend.transcribe)

        assert is_compatible is True

    def test_sync_method_compatibility(self):
        """Test sync method compatibility detection."""
        mock_backend = Mock()
        mock_backend.transcribe = Mock()

        is_compatible = self.resolver._is_compatible_method(mock_backend.transcribe)

        assert is_compatible is True


class TestBackendRegistry:
    """Test backend registry functionality."""

    def setup_method(self):
        self.registry = BackendRegistry()

    def test_backend_registration(self):
        """Test backend registration."""
        mock_backend = Mock()
        config = Mock()
        config.parameters = {}

        self.registry.register_backend(
            BackendType.GEMINI,
            lambda **kwargs: mock_backend,
            config
        )

        assert BackendType.GEMINI in self.registry.backends
        assert BackendType.GEMINI in self.registry.health_status

    def test_backend_retrieval(self):
        """Test backend retrieval."""
        mock_backend = Mock()
        config = Mock()
        config.parameters = {}

        self.registry.register_backend(
            BackendType.GEMINI,
            lambda **kwargs: mock_backend,
            config
        )

        retrieved = self.registry.get_backend(BackendType.GEMINI)

        assert retrieved == mock_backend

    def test_unhealthy_backend_not_returned(self):
        """Test unhealthy backend is not returned."""
        mock_backend = Mock()
        config = Mock()
        config.parameters = {}

        self.registry.register_backend(
            BackendType.GEMINI,
            lambda **kwargs: mock_backend,
            config
        )

        # Mark as unhealthy
        self.registry.update_health(BackendType.GEMINI, False, "Test error")

        retrieved = self.registry.get_backend(BackendType.GEMINI)

        assert retrieved is None

    def test_available_backends_list(self):
        """Test listing available backends."""
        # Register two backends
        mock_backend1 = Mock()
        mock_backend2 = Mock()
        config = Mock()
        config.parameters = {}

        self.registry.register_backend(
            BackendType.GEMINI,
            lambda **kwargs: mock_backend1,
            config
        )
        self.registry.register_backend(
            BackendType.VERTEX,
            lambda **kwargs: mock_backend2,
            config
        )

        available = self.registry.list_available_backends()

        assert BackendType.GEMINI in available
        assert BackendType.VERTEX in available


class TestUnifiedErrorHandler:
    """Test unified error handling functionality."""

    def setup_method(self):
        self.handler = UnifiedErrorHandler()

    def test_error_classification(self):
        """Test error classification."""
        # Test ValueError
        error = ValueError("test error")
        error_type = self.handler._classify_error(error)

        assert error_type == "VALIDATION_ERROR"

    def test_retry_with_backoff_strategy(self):
        """Test retry with backoff strategy."""
        error = Exception("test")
        result = self.handler._retry_with_backoff(
            error, BackendType.GEMINI, {}, {"retry_count": 1}
        )

        assert result["strategy"] == "RETRY_BACKOFF"
        assert result["should_retry"] is True
        assert "backoff_seconds" in result

    def test_switch_backend_strategy(self):
        """Test switch backend strategy."""
        error = Exception("test")
        result = self.handler._switch_backend(
            error, BackendType.GEMINI, {}, {}
        )

        assert result["strategy"] == "SWITCH_BACKEND"
        assert result["should_retry"] is True
        assert "new_backend" in result

    def test_default_recovery_strategy(self):
        """Test default recovery strategy."""
        error = Exception("test")
        result = self.handler._default_recovery(
            error, BackendType.GEMINI, {}, {}
        )

        assert result["strategy"] == "FAIL_FAST"
        assert result["should_retry"] is False


class TestMetricsCollector:
    """Test metrics collection functionality."""

    def setup_method(self):
        self.metrics = MetricsCollector()

    def test_request_recording(self):
        """Test request recording."""
        self.metrics.record_request(BackendType.GEMINI)

        summary = self.metrics.get_summary()

        assert summary["total_requests"] == 1
        assert summary["requests_by_backend"]["gemini"] == 1

    def test_error_recording(self):
        """Test error recording."""
        self.metrics.record_error("TEST_ERROR")

        summary = self.metrics.get_summary()

        assert summary["total_errors"] == 1
        assert summary["errors_by_type"]["TEST_ERROR"] == 1

    def test_response_time_recording(self):
        """Test response time recording."""
        self.metrics.record_response_time(1.5)
        self.metrics.record_response_time(2.0)

        summary = self.metrics.get_summary()

        assert summary["avg_response_time"] == 1.75
        assert summary["max_response_time"] == 2.0
        assert summary["min_response_time"] == 1.5

    def test_backend_switch_recording(self):
        """Test backend switch recording."""
        self.metrics.record_backend_switch()

        summary = self.metrics.get_summary()

        assert summary["backend_switches"] == 1


class TestUnifiedTranscriberAPI:
    """Test the main Unified Transcriber API."""

    def setup_method(self):
        self.api = UnifiedTranscriberAPI()

    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    def test_backend_selection_default(self, mock_gemini_class):
        """Test default backend selection."""
        mock_backend = Mock()
        mock_backend.transcribe = AsyncMock(return_value={"transcript": "test"})
        mock_gemini_class.return_value = mock_backend

        # Re-register to use mock
        from src.clipscribe.api.unified_transcriber import BackendConfig
        config = BackendConfig(
            backend_type=BackendType.GEMINI,
            name="Test Gemini",
            class_path="test",
            parameters={}
        )
        self.api.registry.register_backend(
            BackendType.GEMINI,
            lambda **kwargs: mock_backend,
            config
        )

        backend_type = self.api._select_backend({})

        assert backend_type == BackendType.GEMINI

    def test_sensitive_content_detection(self):
        """Test sensitive content detection."""
        # Sensitive content
        params = {
            "metadata": {
                "title": "Pegasus Spyware Investigation",
                "description": "Military surveillance"
            }
        }

        is_sensitive = self.api._is_sensitive_content(params)

        assert is_sensitive is True

    def test_normal_content_detection(self):
        """Test normal content detection."""
        # Normal content
        params = {
            "metadata": {
                "title": "Cooking Recipe",
                "description": "How to make pasta"
            }
        }

        is_sensitive = self.api._is_sensitive_content(params)

        assert is_sensitive is False

    @patch('src.clipscribe.api.unified_transcriber.Path')
    def test_result_normalization(self, mock_path):
        """Test result normalization."""
        # Mock result
        result = {
            "transcript": "test transcript",
            "entities": [{"name": "Test", "type": "PERSON"}],
            "relationships": []
        }

        normalized = self.api._normalize_result(result, BackendType.GEMINI)

        assert normalized.transcript == "test transcript"
        assert len(normalized.entities) == 1
        assert normalized.entities[0]["name"] == "Test"

    def test_metrics_collection(self):
        """Test metrics collection."""
        # This would be tested in integration tests
        metrics = self.api.get_metrics()

        assert "total_requests" in metrics
        assert "requests_by_backend" in metrics

    def test_backend_health_reporting(self):
        """Test backend health reporting."""
        health = self.api.get_backend_health()

        assert isinstance(health, dict)
        # Should have entries for registered backends


# Integration tests that require more setup
class TestUnifiedAPIIntegration:
    """Integration tests for the unified API."""

    @pytest.mark.asyncio
    async def test_full_transcription_flow(self):
        """Test complete transcription flow."""
        # This would require mocking the actual backends
        # and testing the full pipeline
        pass

    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """Test error recovery and backend switching."""
        # This would test the complete error handling flow
        pass

    @pytest.mark.asyncio
    async def test_parameter_mapping_integration(self):
        """Test parameter mapping in full context."""
        # This would test parameter mapping with real methods
        pass
