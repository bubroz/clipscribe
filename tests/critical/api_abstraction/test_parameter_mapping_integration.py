"""
Integration tests for parameter mapping with real transcribers.

Tests the unified API with actual Gemini and Vertex implementations
to ensure parameter mapping works correctly.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from pathlib import Path

# DEPRECATED: Skip all tests in this file
pytest.skip("These tests are deprecated - Parameter mapping now uses Voxtral-Grok directly, Gemini backend removed", allow_module_level=True)

from src.clipscribe.api.unified_transcriber import (
    UnifiedTranscriberAPI,
    BackendType,
    ParameterMapper
)


class TestParameterMappingIntegration:
    """Test parameter mapping with real transcribers."""

    def setup_method(self):
        self.mapper = ParameterMapper()

    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    def test_gemini_parameter_integration(self, mock_gemini_class):
        """Test parameter mapping works with GeminiFlashTranscriber."""
        # Mock the Gemini transcriber
        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock(return_value={
            "transcript": "test",
            "entities": [],
            "relationships": []
        })
        mock_gemini_class.return_value = mock_transcriber

        # Test parameter mapping
        params = {
            "audio_path": "/test/audio.mp3",
            "duration": 120,
            "metadata": {"title": "Test"}
        }

        mapped = self.mapper.map_parameters(BackendType.GEMINI, params)

        # Verify Gemini parameter mapping
        assert "file_path" in mapped
        assert "duration_seconds" in mapped
        assert "metadata" in mapped
        assert mapped["file_path"] == "/test/audio.mp3"
        assert mapped["duration_seconds"] == 120

    @patch('src.clipscribe.retrievers.vertex_ai_transcriber.VertexAITranscriber')
    def test_vertex_parameter_integration(self, mock_vertex_class):
        """Test parameter mapping works with VertexAITranscriber."""
        # Mock the Vertex transcriber
        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock(return_value={
            "transcript": "test",
            "entities": [],
            "relationships": []
        })
        mock_vertex_class.return_value = mock_transcriber

        # Test parameter mapping
        params = {
            "file_path": "/test/video.mp4",
            "duration": 300,
            "language": "en"
        }

        mapped = self.mapper.map_parameters(BackendType.VERTEX, params)

        # Verify Vertex parameter mapping
        assert "gcs_uri" in mapped
        assert "duration" in mapped
        assert "language" in mapped
        assert mapped["gcs_uri"] == "/test/video.mp4"
        assert mapped["duration"] == 300
        assert mapped["language"] == "en"

    def test_unified_api_parameter_passthrough(self):
        """Test that unified API correctly passes mapped parameters."""
        api = UnifiedTranscriberAPI()

        # Test with Gemini backend (default)
        params = {
            "audio_path": "/test/audio.mp3",
            "duration": 120
        }

        # The unified API should handle parameter mapping internally
        # This test verifies the mapping logic works
        mapped = api.parameter_mapper.map_parameters(BackendType.GEMINI, params)

        assert mapped["file_path"] == "/test/audio.mp3"
        assert mapped["duration_seconds"] == 120


class TestMethodResolutionIntegration:
    """Test method resolution with real transcribers."""

    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    def test_gemini_method_resolution(self, mock_gemini_class):
        """Test method resolution with GeminiFlashTranscriber."""
        # Mock the Gemini transcriber with realistic methods
        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock()
        mock_transcriber.transcribe = AsyncMock()
        mock_gemini_class.return_value = mock_transcriber

        api = UnifiedTranscriberAPI()

        # Test method resolution
        method = api.method_resolver.resolve_method(mock_transcriber, "transcribe")

        # Should resolve to transcribe_video (higher priority than transcribe)
        assert method == mock_transcriber.transcribe_video

    @patch('src.clipscribe.retrievers.vertex_ai_transcriber.VertexAITranscriber')
    def test_vertex_method_resolution(self, mock_vertex_class):
        """Test method resolution with VertexAITranscriber."""
        # Mock the Vertex transcriber
        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock()
        mock_vertex_class.return_value = mock_transcriber

        api = UnifiedTranscriberAPI()

        # Test method resolution
        method = api.method_resolver.resolve_method(mock_transcriber, "transcribe")

        assert method == mock_transcriber.transcribe_video


class TestUnifiedAPIEndToEnd:
    """End-to-end tests for the unified API."""

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    async def test_unified_api_transcription_flow(self, mock_gemini_class):
        """Test complete transcription flow through unified API."""
        # Mock the Gemini transcriber
        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock(return_value={
            "transcript": "Test transcript from unified API",
            "entities": [{"name": "TestEntity", "type": "PERSON", "confidence": 0.9}],
            "relationships": []
        })
        mock_gemini_class.return_value = mock_transcriber

        # Create API instance
        api = UnifiedTranscriberAPI()

        # Execute transcription
        result = await api.transcribe(
            audio_path="/test/audio.mp3",
            duration=120,
            metadata={"title": "Test Video"}
        )

        # Verify result
        assert result.transcript == "Test transcript from unified API"
        assert len(result.entities) == 1
        assert result.entities[0]["name"] == "TestEntity"

        # Verify metrics were recorded
        metrics = api.get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["requests_by_backend"]["gemini"] == 1

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    async def test_backend_selection_logic(self, mock_gemini_class):
        """Test backend selection logic."""
        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock(return_value={"transcript": "test"})
        mock_gemini_class.return_value = mock_transcriber

        api = UnifiedTranscriberAPI()

        # Test default backend selection
        backend = api._select_backend({})
        assert backend == BackendType.GEMINI

        # Test explicit backend selection
        backend = api._select_backend({"backend": "vertex"})
        assert backend == BackendType.VERTEX

    def test_health_reporting(self):
        """Test backend health reporting."""
        api = UnifiedTranscriberAPI()

        health = api.get_backend_health()

        # Should report health for registered backends
        assert isinstance(health, dict)
        assert "gemini" in health
        assert "vertex" in health

        # Check health structure
        gemini_health = health["gemini"]
        assert "healthy" in gemini_health
        assert "last_check" in gemini_health
        assert "error_count" in gemini_health


class TestErrorHandlingIntegration:
    """Test error handling integration."""

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    async def test_error_recovery_flow(self, mock_gemini_class):
        """Test error recovery and retry logic."""
        # Mock transcriber that fails initially then succeeds
        mock_transcriber = Mock()
        call_count = 0

        async def mock_transcribe(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            return {"transcript": "Success after retry"}

        mock_transcriber.transcribe_video = mock_transcribe
        mock_gemini_class.return_value = mock_transcriber

        api = UnifiedTranscriberAPI()

        # This should succeed after retry
        result = await api.transcribe(
            audio_path="/test/audio.mp3",
            duration=120
        )

        assert result.transcript == "Success after retry"
        assert call_count == 2  # One failure, one success

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    async def test_unavailable_backend_handling(self, mock_gemini_class):
        """Test handling when backend is unavailable."""
        # Mock backend that always fails
        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock(side_effect=Exception("Backend unavailable"))
        mock_gemini_class.return_value = mock_transcriber

        api = UnifiedTranscriberAPI()

        # Mark backend as unhealthy
        api.registry.update_health(BackendType.GEMINI, False, "Backend unavailable")

        # Should fail gracefully
        with pytest.raises(RuntimeError, match="Backend gemini not available"):
            await api.transcribe(audio_path="/test/audio.mp3")


class TestPerformanceValidation:
    """Test performance aspects of the unified API."""

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    async def test_parameter_mapping_performance(self, mock_gemini_class):
        """Test parameter mapping performance."""
        import time

        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock(return_value={"transcript": "test"})
        mock_gemini_class.return_value = mock_transcriber

        api = UnifiedTranscriberAPI()

        # Test parameter mapping time
        params = {
            "audio_path": "/test/audio.mp3",
            "duration": 120,
            "metadata": {"title": "Test"},
            "language": "en"
        }

        start_time = time.time()
        for _ in range(100):
            mapped = api.parameter_mapper.map_parameters(BackendType.GEMINI, params)
        end_time = time.time()

        avg_time = (end_time - start_time) / 100

        # Should be very fast (< 1ms per mapping)
        assert avg_time < 0.001

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    async def test_method_resolution_performance(self, mock_gemini_class):
        """Test method resolution performance."""
        import time

        mock_transcriber = Mock()
        mock_transcriber.transcribe_video = AsyncMock(return_value={"transcript": "test"})
        mock_gemini_class.return_value = mock_transcriber

        api = UnifiedTranscriberAPI()

        start_time = time.time()
        for _ in range(100):
            method = api.method_resolver.resolve_method(mock_transcriber, "transcribe")
        end_time = time.time()

        avg_time = (end_time - start_time) / 100

        # Should be very fast (< 1ms per resolution)
        assert avg_time < 0.001
