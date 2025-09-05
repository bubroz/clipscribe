"""
Full integration tests for Grok functionality.

Tests the complete Grok integration workflow including:
- API client functionality
- Transcriber integration
- Unified API fallback
- Cost calculation
- Error handling
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.clipscribe.api.unified_transcriber import UnifiedTranscriberAPI, BackendType
from src.clipscribe.retrievers.grok_transcriber import GrokTranscriber
from src.clipscribe.retrievers.grok_client import GrokAPIClient


class TestGrokFullIntegration:
    """Full integration tests for Grok functionality."""

    @pytest.fixture
    async def grok_client(self):
        """Create a test Grok client."""
        client = GrokAPIClient(api_key="test-key")
        yield client
        await client.client.aclose()

    @pytest.fixture
    def grok_transcriber(self):
        """Create a test Grok transcriber."""
        return GrokTranscriber(api_key="test-key")

    def test_grok_backend_registration(self):
        """Test that Grok backend is properly registered in unified API."""
        api = UnifiedTranscriberAPI()

        # Check that Grok is registered
        grok_backend = api.registry.get_backend(BackendType.GROK)
        assert grok_backend is not None
        assert grok_backend.api_key == "test-key"

        # Check backend configuration
        config = api.registry.configs[BackendType.GROK]
        assert config.backend_type == BackendType.GROK
        assert config.name == "Grok Beta-3"
        assert "GrokTranscriber" in config.class_path

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_grok_transcription_workflow(self, mock_chat_completion, grok_transcriber):
        """Test complete Grok transcription workflow."""
        # Mock API responses
        mock_chat_completion.side_effect = [
            # Transcript generation
            {
                "choices": [
                    {
                        "message": {
                            "content": "This is a comprehensive transcript about AI technology, machine learning, and artificial intelligence applications in modern computing."
                        }
                    }
                ]
            },
            # Intelligence extraction
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "entities": [
                                    {
                                        "name": "AI",
                                        "type": "CONCEPT",
                                        "confidence": 0.95,
                                        "evidence": "Primary topic of discussion",
                                        "quotes": ["AI technology", "artificial intelligence"]
                                    },
                                    {
                                        "name": "Machine Learning",
                                        "type": "CONCEPT",
                                        "confidence": 0.90,
                                        "evidence": "Key technology mentioned",
                                        "quotes": ["machine learning algorithms"]
                                    }
                                ],
                                "relationships": [
                                    {
                                        "subject": "AI",
                                        "predicate": "USES",
                                        "object": "Machine Learning",
                                        "confidence": 0.85,
                                        "evidence": "AI systems use machine learning",
                                        "quotes": ["AI uses machine learning"]
                                    }
                                ]
                            })
                        }
                    }
                ]
            }
        ]

        result = await grok_transcriber.transcribe_video(
            audio_path="/test/ai_video.mp4",
            metadata={
                "title": "AI Technology Overview 2025",
                "description": "Comprehensive overview of artificial intelligence",
                "channel": "Tech Insights",
                "duration": 600
            }
        )

        # Verify result structure
        assert result.metadata.title == "AI Technology Overview 2025"
        assert result.metadata.channel == "Tech Insights"
        assert "AI technology" in result.transcript.full_text
        assert len(result.entities) == 2
        assert len(result.relationships) == 1
        assert result.entities[0].name == "AI"
        assert result.entities[1].name == "Machine Learning"
        assert result.relationships[0].subject == "AI"
        assert result.processing_cost > 0

    @patch('src.clipscribe.retrievers.transcriber.GeminiFlashTranscriber')
    @patch('src.clipscribe.retrievers.grok_transcriber.GrokTranscriber')
    async def test_unified_api_grok_fallback(self, mock_grok_class, mock_gemini_class):
        """Test unified API with Grok fallback for sensitive content."""
        api = UnifiedTranscriberAPI()

        # Mock Gemini failure with safety filter
        mock_gemini = Mock()
        mock_gemini.transcribe_video.side_effect = Exception("finish_reason: 2 - Safety filter blocked content")
        mock_gemini_class.return_value = mock_gemini

        # Mock Grok success
        mock_grok = Mock()
        mock_grok_result = Mock()
        mock_grok_result.transcript = Mock(full_text="Grok processed sensitive intelligence content")
        mock_grok_result.entities = []
        mock_grok_result.relationships = []
        mock_grok_result.metadata = Mock(title="Intelligence Report")
        mock_grok_result.processing_cost = 0.015
        mock_grok.transcribe_video = AsyncMock(return_value=mock_grok_result)
        mock_grok_class.return_value = mock_grok

        result = await api.transcribe(
            audio_path="/test/intelligence.mp4",
            metadata={
                "title": "Classified Intelligence Briefing",
                "description": "Sensitive military intelligence analysis",
                "channel": "Defense Intelligence"
            }
        )

        # Verify fallback occurred
        assert mock_gemini.transcribe_video.called
        assert mock_grok.transcribe_video.called
        assert "Grok processed sensitive intelligence" in result.transcript.full_text

        # Verify metrics recorded the switch
        metrics = api.get_metrics()
        assert metrics["backend_switches"] == 1

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_grok_cost_calculation_accuracy(self, mock_chat_completion, grok_transcriber):
        """Test that Grok cost calculation is accurate."""
        # Mock simple response
        mock_chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Short response"
                    }
                }
            ]
        }

        # Mock both calls
        with patch.object(grok_transcriber.client, 'chat_completion', side_effect=[
            mock_chat_completion.return_value,
            mock_chat_completion.return_value
        ]):
            result = await grok_transcriber.transcribe_video(
                audio_path="/test/video.mp4",
                metadata={"title": "Test"}
            )

        # Verify cost is calculated (exact value depends on token estimation)
        assert result.processing_cost > 0
        assert isinstance(result.processing_cost, float)

        # Test cost calculation directly
        client = GrokAPIClient(api_key="test")
        cost = client.calculate_cost(1000, 500, "grok-beta-3")
        expected_cost = (1000/1000 * 0.005) + (500/1000 * 0.015)  # 0.005 + 0.0075 = 0.0125
        assert cost == expected_cost

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_grok_error_handling_and_recovery(self, mock_chat_completion, grok_transcriber):
        """Test Grok error handling and recovery."""
        # Mock API error on first call, success on second
        mock_chat_completion.side_effect = [
            Exception("Rate limit exceeded"),  # First call fails
            {  # Second call succeeds
                "choices": [
                    {
                        "message": {
                            "content": "Success after retry"
                        }
                    }
                ]
            }
        ]

        with patch.object(grok_transcriber.client, 'chat_completion', side_effect=mock_chat_completion.side_effect):
            result = await grok_transcriber.transcribe_video(
                audio_path="/test/video.mp4",
                metadata={"title": "Test"}
            )

        assert "Success after retry" in result.transcript.full_text

    def test_grok_parameter_mapping_integration(self):
        """Test that Grok parameters are properly mapped in unified API."""
        api = UnifiedTranscriberAPI()

        # Test parameter mapping for Grok
        params = {
            "audio_path": "/test/audio.mp3",
            "duration": 120,
            "language": "en"
        }

        mapped = api.parameter_mapper.map_parameters(BackendType.GROK, params)

        assert "content_path" in mapped
        assert "length" in mapped
        assert "lang" in mapped
        assert mapped["content_path"] == "/test/audio.mp3"
        assert mapped["length"] == 120
        assert mapped["lang"] == "en"

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.list_models')
    async def test_grok_health_check_integration(self, mock_list_models):
        """Test Grok health check integration."""
        mock_list_models.return_value = {"models": ["grok-beta-3", "grok-3"]}

        transcriber = GrokTranscriber(api_key="test-key")
        is_healthy = await transcriber.health_check()

        assert is_healthy is True

    async def test_grok_client_context_manager(self):
        """Test Grok client context manager."""
        async with GrokAPIClient(api_key="test-key") as client:
            assert client.api_key == "test-key"
            assert client.client is not None

        # Client should be closed after context
        assert client.client.is_closed

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_grok_sensitive_content_processing(self, mock_chat_completion, grok_transcriber):
        """Test Grok's ability to process sensitive content without censorship."""
        # Mock response with sensitive content
        sensitive_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "entities": [
                                {
                                    "name": "Surveillance",
                                    "type": "CONCEPT",
                                    "confidence": 0.95,
                                    "evidence": "Primary topic of investigative journalism",
                                    "quotes": ["government surveillance programs"]
                                },
                                {
                                    "name": "NSO Group",
                                    "type": "ORGANIZATION",
                                    "confidence": 0.90,
                                    "evidence": "Company mentioned in investigation",
                                    "quotes": ["NSO Group spyware"]
                                }
                            ],
                            "relationships": [
                                {
                                    "subject": "NSO Group",
                                    "predicate": "DEVELOPS",
                                    "object": "Surveillance",
                                    "confidence": 0.85,
                                    "evidence": "Company develops surveillance technology",
                                    "quotes": ["NSO Group develops spyware"]
                                }
                            ]
                        })
                    }
                }
            ]
        }

        mock_chat_completion.side_effect = [
            # Transcript generation
            {
                "choices": [
                    {
                        "message": {
                            "content": "Transcript about Pegasus spyware and government surveillance programs used by NSO Group."
                        }
                    }
                ]
            },
            # Intelligence extraction
            sensitive_response
        ]

        result = await grok_transcriber.transcribe_video(
            audio_path="/test/pegasus.mp4",
            metadata={
                "title": "Pegasus Spyware Investigation",
                "description": "Investigation into NSO Group surveillance technology",
                "channel": "Al Jazeera Investigations"
            }
        )

        # Verify sensitive content was processed without censorship
        assert "Pegasus" in result.transcript.full_text
        assert len(result.entities) == 2
        assert len(result.relationships) == 1
        assert result.entities[0].name == "Surveillance"
        assert result.entities[1].name == "NSO Group"
        assert result.relationships[0].subject == "NSO Group"

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_grok_json_error_recovery(self, mock_chat_completion, grok_transcriber):
        """Test recovery from malformed JSON responses."""
        mock_chat_completion.side_effect = [
            # Good transcript
            {
                "choices": [
                    {
                        "message": {
                            "content": "Valid transcript content"
                        }
                    }
                ]
            },
            # Bad JSON in intelligence extraction
            {
                "choices": [
                    {
                        "message": {
                            "content": "Invalid JSON response {{{ not valid"
                        }
                    }
                ]
            }
        ]

        result = await grok_transcriber.transcribe_video(
            audio_path="/test/video.mp4",
            metadata={"title": "Test Video"}
        )

        # Should still succeed with empty entities/relationships
        assert result.transcript.full_text == "Valid transcript content"
        assert result.entities == []
        assert result.relationships == []

    def test_grok_backend_health_reporting(self):
        """Test Grok backend health reporting in unified API."""
        api = UnifiedTranscriberAPI()

        health = api.get_backend_health()

        # Should include Grok backend
        assert "grok" in health
        grok_health = health["grok"]

        # Health should have required fields
        assert "healthy" in grok_health
        assert "last_check" in grok_health
        assert "error_count" in grok_health
        assert "last_error" in grok_health

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_grok_processing_cost_tracking(self, mock_chat_completion, grok_transcriber):
        """Test that Grok processing costs are properly tracked."""
        mock_chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ]
        }

        with patch.object(grok_transcriber.client, 'chat_completion', side_effect=[
            mock_chat_completion.return_value,
            mock_chat_completion.return_value
        ]):
            result = await grok_transcriber.transcribe_video(
                audio_path="/test/video.mp4",
                metadata={"title": "Cost Test Video"}
            )

        # Cost should be calculated and tracked
        assert result.processing_cost > 0
        assert result.processing_time >= 0

        # Cost should be reasonable for Grok pricing
        assert result.processing_cost < 1.0  # Should be much less than $1 for test content
