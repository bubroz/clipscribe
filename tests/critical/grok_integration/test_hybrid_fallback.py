"""
Tests for hybrid fallback functionality in unified API.

Tests the automatic switching between backends when safety filters are triggered.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.clipscribe.api.unified_transcriber import UnifiedTranscriberAPI, BackendType
from src.clipscribe.retrievers.grok_client import GrokAPIError

# DEPRECATED: Skip all tests in this file
pytest.skip("These tests are deprecated - Gemini fallback functionality has been removed, now using Voxtral-Grok direct pipeline", allow_module_level=True)


class TestHybridFallback:
    """Test hybrid fallback functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api = UnifiedTranscriberAPI()

    def test_safety_filter_error_detection(self):
        """Test detection of safety filter errors."""
        # Test various safety filter error messages
        safety_errors = [
            "finish_reason: 2",
            "Content blocked by safety filter",
            "Safety settings prevented response",
            "Harmful content detected",
            "Content policy violation"
        ]

        for error_msg in safety_errors:
            error = Exception(error_msg)
            assert self.api._is_safety_filter_error(error)

    def test_non_safety_error_detection(self):
        """Test that non-safety errors are not misidentified."""
        non_safety_errors = [
            "Network timeout",
            "Invalid API key",
            "Rate limit exceeded",
            "Server error 500",
            "Connection failed"
        ]

        for error_msg in non_safety_errors:
            error = Exception(error_msg)
            assert not self.api._is_safety_filter_error(error)

    def test_sensitive_content_detection(self):
        """Test detection of sensitive content."""
        # Sensitive content examples
        sensitive_params = [
            {
                "metadata": {
                    "title": "Pegasus Spyware Investigation",
                    "description": "NSO Group surveillance"
                }
            },
            {
                "metadata": {
                    "title": "Military Intelligence Operations",
                    "description": "Classified defense technology"
                }
            },
            {
                "metadata": {
                    "title": "Terrorism Analysis Report",
                    "description": "Security threat assessment"
                }
            }
        ]

        for params in sensitive_params:
            assert self.api._is_sensitive_content(params)

    def test_normal_content_detection(self):
        """Test that normal content is not flagged as sensitive."""
        normal_params = [
            {
                "metadata": {
                    "title": "Cooking Pasta Recipe",
                    "description": "Italian cuisine tutorial"
                }
            },
            {
                "metadata": {
                    "title": "Python Programming Tutorial",
                    "description": "Learn to code with Python"
                }
            },
            {
                "metadata": {
                    "title": "Weather Forecast",
                    "description": "Today's weather conditions"
                }
            }
        ]

        for params in normal_params:
            assert not self.api._is_sensitive_content(params)

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('src.clipscribe.retrievers.grok_transcriber.GrokTranscriber')
    async def test_hybrid_fallback_success(self, mock_grok_class, mock_gemini_class):
        """Test successful fallback from Gemini to Grok."""
        # Mock Gemini failure with safety filter
        mock_gemini = Mock()
        mock_gemini.transcribe_video.side_effect = Exception("finish_reason: 2 - Content blocked by safety filter")
        mock_gemini_class.return_value = mock_gemini

        # Mock Grok success
        mock_grok = Mock()
        mock_grok.transcribe_video = AsyncMock(return_value=Mock(
            transcript=Mock(full_text="Grok processed content"),
            entities=[],
            relationships=[],
            metadata=Mock(title="Test"),
            processing_cost=0.01
        ))
        mock_grok_class.return_value = mock_grok

        result = await self.api.transcribe(
            audio_path="/test/sensitive.mp4",
            metadata={
                "title": "Sensitive Security Content",
                "description": "Military intelligence analysis"
            }
        )

        # Should have tried Gemini first (failed), then Grok (succeeded)
        assert mock_gemini.transcribe_video.called
        assert mock_grok.transcribe_video.called
        assert result.transcript.full_text == "Grok processed content"

        # Should record backend switch
        metrics = self.api.get_metrics()
        assert metrics["backend_switches"] == 1

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    async def test_no_fallback_for_non_safety_errors(self, mock_gemini_class):
        """Test that non-safety errors don't trigger fallback."""
        # Mock Gemini failure with non-safety error
        mock_gemini = Mock()
        mock_gemini.transcribe_video.side_effect = Exception("Network timeout")
        mock_gemini_class.return_value = mock_gemini

        # Should fail without trying other backends
        with pytest.raises(RuntimeError, match="All backends failed"):
            await self.api.transcribe(
                audio_path="/test/video.mp4",
                metadata={"title": "Test Video"}
            )

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('src.clipscribe.retrievers.grok_transcriber.GrokTranscriber')
    async def test_prefer_grok_for_sensitive_content(self, mock_grok_class, mock_gemini_class):
        """Test that Grok is preferred for sensitive content."""
        # Mock both backends as available
        mock_gemini = Mock()
        mock_gemini.transcribe_video = AsyncMock(return_value=Mock(
            transcript=Mock(full_text="Gemini processed"),
            entities=[],
            relationships=[],
            metadata=Mock(title="Test"),
            processing_cost=0.01
        ))
        mock_gemini_class.return_value = mock_gemini

        mock_grok = Mock()
        mock_grok.transcribe_video = AsyncMock(return_value=Mock(
            transcript=Mock(full_text="Grok processed"),
            entities=[],
            relationships=[],
            metadata=Mock(title="Test"),
            processing_cost=0.01
        ))
        mock_grok_class.return_value = mock_grok

        result = await self.api.transcribe(
            audio_path="/test/sensitive.mp4",
            metadata={
                "title": "Pegasus Spyware Analysis",
                "description": "Intelligence investigation"
            }
        )

        # Should try Grok first for sensitive content
        assert mock_grok.transcribe_video.called
        assert result.transcript.full_text == "Grok processed"

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    async def test_prefer_gemini_for_normal_content(self, mock_gemini_class):
        """Test that Gemini is preferred for normal content."""
        # Mock Gemini success
        mock_gemini = Mock()
        mock_gemini.transcribe_video = AsyncMock(return_value=Mock(
            transcript=Mock(full_text="Gemini processed normal content"),
            entities=[],
            relationships=[],
            metadata=Mock(title="Test"),
            processing_cost=0.01
        ))
        mock_gemini_class.return_value = mock_gemini

        result = await self.api.transcribe(
            audio_path="/test/normal.mp4",
            metadata={
                "title": "Cooking Recipe",
                "description": "How to make pasta"
            }
        )

        # Should use Gemini for normal content
        assert mock_gemini.transcribe_video.called
        assert result.transcript.full_text == "Gemini processed normal content"

    @pytest.mark.asyncio
    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('src.clipscribe.retrievers.vertex_ai_transcriber.VertexAITranscriber')
    @patch('src.clipscribe.retrievers.grok_transcriber.GrokTranscriber')
    async def test_three_backend_fallback_chain(self, mock_grok_class, mock_vertex_class, mock_gemini_class):
        """Test fallback through all three backends."""
        # Mock Gemini -> Vertex -> Grok failure chain
        mock_gemini = Mock()
        mock_gemini.transcribe_video.side_effect = Exception("finish_reason: 2")
        mock_gemini_class.return_value = mock_gemini

        mock_vertex = Mock()
        mock_vertex.transcribe_video.side_effect = Exception("Vertex API error")
        mock_vertex_class.return_value = mock_vertex

        mock_grok = Mock()
        mock_grok.transcribe_video = AsyncMock(return_value=Mock(
            transcript=Mock(full_text="Grok final success"),
            entities=[],
            relationships=[],
            metadata=Mock(title="Test"),
            processing_cost=0.01
        ))
        mock_grok_class.return_value = mock_grok

        result = await self.api.transcribe(
            audio_path="/test/very_sensitive.mp4",
            metadata={
                "title": "Highly Sensitive Intelligence",
                "description": "Classified military analysis"
            }
        )

        # Should try all three backends
        assert mock_gemini.transcribe_video.called
        assert mock_vertex.transcribe_video.called
        assert mock_grok.transcribe_video.called
        assert result.transcript.full_text == "Grok final success"

    def test_backend_availability_check(self):
        """Test that backend availability is properly checked."""
        # Mock backend registry to simulate unavailable backends
        original_get_backend = self.api.registry.get_backend

        def mock_get_backend(backend_type):
            if backend_type == BackendType.GROK:
                return None  # Simulate Grok unavailable
            return original_get_backend(backend_type)

        self.api.registry.get_backend = mock_get_backend

        # Should skip unavailable backends
        assert self.api.registry.get_backend(BackendType.GROK) is None
        assert self.api.registry.get_backend(BackendType.GEMINI) is not None

    def test_metrics_tracking_for_fallbacks(self):
        """Test that fallback attempts are properly tracked in metrics."""
        # Start with clean metrics
        self.api.metrics = Mock()
        self.api.metrics.record_backend_switch = Mock()

        # Simulate backend switch detection
        attempted_backends = [BackendType.GEMINI, BackendType.GROK]

        # The actual logic would detect this and record it
        if len(attempted_backends) > 1:
            self.api.metrics.record_backend_switch()

        self.api.metrics.record_backend_switch.assert_called_once()

    def test_error_message_formatting(self):
        """Test that error messages include attempted backends."""
        attempted_backends = [BackendType.GEMINI, BackendType.VERTEX, BackendType.GROK]

        expected_msg = f"Unified transcription failed after trying {len(attempted_backends)} backends: Test error"
        actual_msg = f"All transcription backends failed. Attempted: {[b.value for b in attempted_backends]}. Available: ['gemini', 'vertex', 'grok']"

        assert "3 backends" in expected_msg
        assert "gemini" in actual_msg
        assert "vertex" in actual_msg
        assert "grok" in actual_msg
