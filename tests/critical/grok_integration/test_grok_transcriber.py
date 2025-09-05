"""
Tests for Grok transcriber integration.

Tests the GrokTranscriber with mocked API responses.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from src.clipscribe.retrievers.grok_transcriber import GrokTranscriber
from src.clipscribe.retrievers.grok_client import GrokAPIClient


class TestGrokTranscriber:
    """Test Grok transcriber functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test-xai-key"
        self.transcriber = GrokTranscriber(api_key=self.api_key)

    def test_transcriber_initialization(self):
        """Test transcriber initialization."""
        assert self.transcriber.api_key == self.api_key
        assert self.transcriber.model == "grok-beta-3"
        assert isinstance(self.transcriber.client, GrokAPIClient)

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_transcribe_video_success(self, mock_chat_completion):
        """Test successful video transcription."""
        # Mock the chat completion response
        mock_chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a generated transcript for the video about AI technology."
                    }
                }
            ]
        }

        # Mock intelligence extraction response
        with patch.object(self.transcriber.client, 'chat_completion', side_effect=[
            # First call for transcript
            {
                "choices": [
                    {
                        "message": {
                            "content": "Generated transcript about AI technology and machine learning."
                        }
                    }
                ]
            },
            # Second call for intelligence extraction
            {
                "choices": [
                    {
                        "message": {
                            "content": '''{
                            "entities": [
                                {
                                    "name": "AI",
                                    "type": "CONCEPT",
                                    "confidence": 0.95,
                                    "evidence": "Main topic of the video",
                                    "quotes": ["AI technology"]
                                }
                            ],
                            "relationships": [
                                {
                                    "subject": "AI",
                                    "predicate": "ENABLES",
                                    "object": "Machine Learning",
                                    "confidence": 0.9,
                                    "evidence": "AI enables machine learning",
                                    "quotes": ["AI enables machine learning"]
                                }
                            ]
                        }'''
                        }
                    }
                ]
            }
        ]):
            result = await self.transcriber.transcribe_video(
                audio_path="/test/video.mp4",
                metadata={
                    "title": "AI Technology Overview",
                    "channel": "Tech Channel",
                    "duration": 300
                }
            )

        assert result.metadata.title == "AI Technology Overview"
        assert result.metadata.channel == "Tech Channel"
        assert "Generated transcript" in result.transcript.full_text
        assert len(result.entities) == 1
        assert len(result.relationships) == 1
        assert result.entities[0].name == "AI"
        assert result.processing_cost > 0

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_transcribe_video_with_sensitive_content(self, mock_chat_completion):
        """Test transcription with sensitive content keywords."""
        # Mock responses
        mock_chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Transcript about security and surveillance technology."
                    }
                }
            ]
        }

        with patch.object(self.transcriber.client, 'chat_completion', side_effect=[
            {
                "choices": [
                    {
                        "message": {
                            "content": "Security transcript content."
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "content": '''{
                            "entities": [
                                {
                                    "name": "Security",
                                    "type": "CONCEPT",
                                    "confidence": 0.95
                                }
                            ],
                            "relationships": []
                        }'''
                        }
                    }
                ]
            }
        ]):
            result = await self.transcriber.transcribe_video(
                audio_path="/test/video.mp4",
                metadata={
                    "title": "Advanced Security and Surveillance",
                    "description": "Military-grade security technology",
                    "channel": "Defense Tech"
                }
            )

        assert "Security" in result.transcript.full_text

    def test_missing_api_key_error(self):
        """Test error when API key is missing."""
        with pytest.raises(ValueError, match="xAI API key is required"):
            GrokTranscriber(api_key="")

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.list_models')
    async def test_health_check_success(self, mock_list_models):
        """Test successful health check."""
        mock_list_models.return_value = {"models": ["grok-beta-3"]}

        is_healthy = await self.transcriber.health_check()

        assert is_healthy is True

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.list_models')
    async def test_health_check_failure(self, mock_list_models):
        """Test failed health check."""
        mock_list_models.side_effect = Exception("Connection failed")

        is_healthy = await self.transcriber.health_check()

        assert is_healthy is False

    def test_cost_calculation(self):
        """Test cost calculation for processing."""
        transcript = "This is a test transcript with some content."
        entities = [{"name": "Test"}]
        relationships = [{"subject": "A", "predicate": "relates", "object": "B"}]

        cost = self.transcriber._calculate_cost(transcript, entities, relationships)

        # Should calculate cost based on token estimates
        assert cost > 0
        assert isinstance(cost, float)

    def test_enhanced_analysis_prompt_structure(self):
        """Test that enhanced analysis prompts are properly structured."""
        transcript = "Test transcript content"
        metadata = {
            "title": "Test Video",
            "description": "Test description"
        }

        prompt = self.transcriber._build_enhanced_analysis_prompt(transcript, metadata)

        # Verify prompt contains required elements
        assert "Test Video" in prompt
        assert "Test description" in prompt
        assert transcript in prompt
        assert "entities" in prompt
        assert "relationships" in prompt
        assert "JSON" in prompt
        assert "uncensored" in prompt

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_api_error_handling(self, mock_chat_completion):
        """Test handling of API errors."""
        from src.clipscribe.retrievers.grok_client import GrokAPIError

        mock_chat_completion.side_effect = GrokAPIError("API error")

        with pytest.raises(GrokAPIError):
            await self.transcriber.transcribe_video(
                audio_path="/test/video.mp4",
                metadata={"title": "Test"}
            )

    @patch('src.clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion')
    async def test_json_parsing_error_recovery(self, mock_chat_completion):
        """Test recovery from JSON parsing errors."""
        # Mock invalid JSON response
        mock_chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Invalid JSON response {{{"
                    }
                }
            ]
        }

        with patch.object(self.transcriber.client, 'chat_completion', side_effect=[
            # Transcript call succeeds
            {
                "choices": [
                    {
                        "message": {
                            "content": "Valid transcript"
                        }
                    }
                ]
            },
            # Intelligence extraction fails with invalid JSON
            {
                "choices": [
                    {
                        "message": {
                            "content": "Invalid JSON {{{"
                        }
                    }
                ]
            }
        ]):
            result = await self.transcriber.transcribe_video(
                audio_path="/test/video.mp4",
                metadata={"title": "Test"}
            )

            # Should still return result with empty entities/relationships
            assert result.entities == []
            assert result.relationships == []
            assert result.transcript.full_text == "Valid transcript"
