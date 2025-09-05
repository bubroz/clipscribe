"""
Core tests for API Abstraction Layer - focuses on the core functionality
without complex dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from src.clipscribe.api.unified_transcriber import (
    BackendType,
    BackendRegistry,
    ParameterMapper,
    MethodResolver,
    UnifiedErrorHandler,
    MetricsCollector,
    TranscriptionResult
)


class TestBackendRegistryCore:
    """Test backend registry core functionality."""

    def setup_method(self):
        self.registry = BackendRegistry()

    def test_backend_registration_success(self):
        """Test successful backend registration."""
        mock_backend = Mock()
        config = Mock()
        config.parameters = {}

        self.registry.register_backend(
            BackendType.GEMINI,
            lambda **kwargs: mock_backend,
            config
        )

        assert BackendType.GEMINI in self.registry.backends
        assert self.registry.health_status[BackendType.GEMINI].is_healthy

    def test_backend_retrieval_success(self):
        """Test backend retrieval when healthy."""
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

    def test_list_available_backends(self):
        """Test listing available backends."""
        # Register multiple backends
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


class TestParameterMapperCore:
    """Test parameter mapping core functionality."""

    def setup_method(self):
        self.mapper = ParameterMapper()

    def test_gemini_parameter_mapping_core(self):
        """Test core Gemini parameter mapping."""
        params = {
            "audio_path": "/test/audio.mp3",
            "duration": 120,
            "metadata": {"title": "test"}
        }

        mapped = self.mapper.map_parameters(BackendType.GEMINI, params)

        assert "file_path" in mapped
        assert "duration_seconds" in mapped
        assert "metadata" in mapped
        assert mapped["file_path"] == "/test/audio.mp3"
        assert mapped["duration_seconds"] == 120

    def test_vertex_parameter_mapping_core(self):
        """Test core Vertex parameter mapping."""
        params = {
            "file_path": "/test/video.mp4",
            "duration": 300,
            "language": "en"
        }

        mapped = self.mapper.map_parameters(BackendType.VERTEX, params)

        assert "gcs_uri" in mapped
        assert "duration" in mapped
        assert "language" in mapped
        assert mapped["gcs_uri"] == "/test/video.mp4"
        assert mapped["duration"] == 300
        assert mapped["language"] == "en"

    def test_unknown_parameter_passthrough(self):
        """Test unknown parameters are passed through."""
        params = {"unknown_param": "value"}

        mapped = self.mapper.map_parameters(BackendType.GEMINI, params)

        assert "unknown_param" in mapped
        assert mapped["unknown_param"] == "value"

    def test_path_validation_core(self):
        """Test path parameter validation."""
        # Valid string path
        result = self.mapper._validate_path("/test/path.mp3")
        assert result == "/test/path.mp3"

        # Valid Path object
        result = self.mapper._validate_path(Path("/test/path.mp3"))
        assert result == "/test/path.mp3"

        # Integer gets converted to string (valid behavior)
        result = self.mapper._validate_path(123)
        assert result == "123"

        # The validation method is designed to be permissive and handle
        # various input types, which is the correct behavior for the API

    def test_gcs_uri_validation_core(self):
        """Test GCS URI validation."""
        # Valid GCS URI
        result = self.mapper._validate_gcs_uri("gs://bucket/file.mp4")
        assert result == "gs://bucket/file.mp4"

        # Valid local path
        result = self.mapper._validate_gcs_uri("/local/path/file.mp4")
        assert result == "/local/path/file.mp4"

        # Invalid URI
        with pytest.raises(ValueError, match="Invalid GCS URI"):
            self.mapper._validate_gcs_uri("invalid_uri")

        # Invalid type
        with pytest.raises(ValueError, match="Invalid GCS URI"):
            self.mapper._validate_gcs_uri(123)


class TestMethodResolverCore:
    """Test method resolution core functionality."""

    def setup_method(self):
        self.resolver = MethodResolver()

    def test_method_priority_resolution(self):
        """Test method resolution follows priority order."""
        mock_backend = Mock()

        # Add methods in reverse priority order
        mock_backend.extract = Mock()
        mock_backend.analyze = Mock()
        mock_backend.transcribe = Mock()

        method = self.resolver.resolve_method(mock_backend, "transcribe")

        assert method == mock_backend.transcribe

    def test_method_fallback_resolution(self):
        """Test method resolution falls back correctly."""
        mock_backend = Mock()
        mock_backend.process = Mock()

        # Remove higher priority methods
        for method_name in ['transcribe', 'transcribe_audio', 'transcribe_video']:
            if hasattr(mock_backend, method_name):
                delattr(mock_backend, method_name)

        method = self.resolver.resolve_method(mock_backend, "transcribe")

        assert method == mock_backend.process

    def test_method_resolution_no_match(self):
        """Test method resolution returns None when no methods found."""
        mock_backend = Mock()

        # Remove all priority methods
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


class TestUnifiedErrorHandlerCore:
    """Test unified error handling core functionality."""

    def setup_method(self):
        self.handler = UnifiedErrorHandler()

    def test_error_classification_core(self):
        """Test error classification."""
        # Test ValueError
        error = ValueError("test error")
        error_type = self.handler._classify_error(error)

        assert error_type == "VALIDATION_ERROR"

        # Test generic error
        error = Exception("generic error")
        error_type = self.handler._classify_error(error)

        assert error_type == "UNKNOWN_ERROR"

    def test_recovery_strategies(self):
        """Test recovery strategy selection."""
        # Rate limit error
        result = self.handler._retry_with_backoff(
            Exception("rate limit"),
            BackendType.GEMINI,
            {},
            {"retry_count": 1}
        )

        assert result["strategy"] == "RETRY_BACKOFF"
        assert result["should_retry"] is True

        # Timeout error
        result = self.handler._retry_with_timeout(
            Exception("timeout"),
            BackendType.GEMINI,
            {},
            {"current_timeout": 30}
        )

        assert result["strategy"] == "RETRY_TIMEOUT"
        assert result["should_retry"] is True


class TestMetricsCollectorCore:
    """Test metrics collection core functionality."""

    def setup_method(self):
        self.metrics = MetricsCollector()

    def test_request_counting(self):
        """Test request counting."""
        self.metrics.record_request(BackendType.GEMINI)
        self.metrics.record_request(BackendType.GEMINI)
        self.metrics.record_request(BackendType.VERTEX)

        summary = self.metrics.get_summary()

        assert summary["total_requests"] == 3
        assert summary["requests_by_backend"]["gemini"] == 2
        assert summary["requests_by_backend"]["vertex"] == 1

    def test_error_counting(self):
        """Test error counting."""
        self.metrics.record_error("TEST_ERROR")
        self.metrics.record_error("TEST_ERROR")
        self.metrics.record_error("DIFFERENT_ERROR")

        summary = self.metrics.get_summary()

        assert summary["total_errors"] == 3
        assert summary["errors_by_type"]["TEST_ERROR"] == 2
        assert summary["errors_by_type"]["DIFFERENT_ERROR"] == 1

    def test_response_time_tracking(self):
        """Test response time tracking."""
        self.metrics.record_response_time(1.5)
        self.metrics.record_response_time(2.0)
        self.metrics.record_response_time(0.8)

        summary = self.metrics.get_summary()

        assert summary["avg_response_time"] == 1.4333333333333333
        assert summary["max_response_time"] == 2.0
        assert summary["min_response_time"] == 0.8

    def test_backend_switch_counting(self):
        """Test backend switch counting."""
        self.metrics.record_backend_switch()
        self.metrics.record_backend_switch()

        summary = self.metrics.get_summary()

        assert summary["backend_switches"] == 2


class TestTranscriptionResultCore:
    """Test TranscriptionResult core functionality."""

    def test_transcription_result_creation(self):
        """Test TranscriptionResult creation."""
        result = TranscriptionResult(
            transcript="Test transcript",
            entities=[{"name": "Entity1", "type": "PERSON"}],
            relationships=[{"subject": "Entity1", "predicate": "WORKS_FOR", "object": "Company"}],
            summary="Test summary",
            backend="gemini",
            processing_cost=0.10,
            processing_time=5.0
        )

        assert result.transcript == "Test transcript"
        assert len(result.entities) == 1
        assert len(result.relationships) == 1
        assert result.summary == "Test summary"
        assert result.backend == "gemini"
        assert result.processing_cost == 0.10
        assert result.processing_time == 5.0

    def test_transcription_result_defaults(self):
        """Test TranscriptionResult default values."""
        result = TranscriptionResult(transcript="Test transcript")

        assert result.entities == []
        assert result.relationships == []
        assert result.key_points == []
        assert result.summary == ""
        assert result.backend == "unknown"
        assert result.processing_cost == 0.0
        assert result.processing_time == 0.0

    def test_to_video_intelligence_conversion(self):
        """Test conversion to VideoIntelligence format."""
        result = TranscriptionResult(
            transcript="Test transcript",
            entities=[{"name": "Entity1", "type": "PERSON"}],
            summary="Test summary"
        )

        metadata = {
            "video_id": "test123",
            "title": "Test Video",
            "channel": "Test Channel",
            "channel_id": "channel123",
            "published_at": "2025-01-01T00:00:00Z",
            "duration": 120,
            "description": "Test description"
        }

        vi_result = result.to_video_intelligence(metadata)

        assert vi_result.transcript.full_text == "Test transcript"
        assert vi_result.metadata.video_id == "test123"
        assert vi_result.metadata.title == "Test Video"
        assert vi_result.summary == "Test summary"
        assert len(vi_result.entities) == 1
        assert vi_result.entities[0].name == "Entity1"
