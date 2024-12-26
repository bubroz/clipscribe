"""Tests for transcription functionality."""

import os
import pytest
from unittest.mock import Mock, patch
from google.cloud import speech_v2
from src.transcription import SpeechRecognizer, TranscriptProcessor
from src.error_handling import TranscriptionError

@pytest.fixture
def speech_recognizer():
    """Fixture for SpeechRecognizer instance."""
    with patch('google.cloud.speech_v2.SpeechClient') as mock_client:
        recognizer = SpeechRecognizer("test-project")
        recognizer.client = mock_client
        yield recognizer

@pytest.fixture
def transcript_processor():
    """Fixture for TranscriptProcessor instance."""
    return TranscriptProcessor()

@pytest.fixture
def mock_response():
    """Fixture for mock transcription response."""
    return {
        "results": {
            "file1": {
                "transcript": {
                    "results": [
                        {
                            "alternatives": [
                                {
                                    "transcript": "This is a test transcript.",
                                    "confidence": 0.95,
                                    "words": [
                                        {
                                            "word": "This",
                                            "confidence": 0.96,
                                            "startOffset": "0.0s",
                                            "endOffset": "0.4s"
                                        },
                                        {
                                            "word": "is",
                                            "confidence": 0.97,
                                            "startOffset": "0.4s",
                                            "endOffset": "0.6s"
                                        }
                                    ]
                                }
                            ],
                            "languageCode": "en-US"
                        }
                    ]
                }
            }
        }
    }

def test_create_recognition_config(speech_recognizer):
    """Test recognition config creation."""
    config = speech_recognizer.create_recognition_config("test.wav")
    
    assert isinstance(config, speech_v2.RecognitionConfig)
    assert config.language_codes == ["en-US"]
    assert config.model == "latest_long"

def test_process_response_success(transcript_processor, mock_response):
    """Test successful response processing."""
    result = transcript_processor.process_response(mock_response)
    
    assert result["transcript"].strip() == "This is a test transcript."
    assert result["confidence"] == 0.95
    assert result["language_code"] == "en-US"
    assert len(result["words"]) == 2

def test_process_response_empty(transcript_processor):
    """Test processing empty response."""
    with pytest.raises(TranscriptionError, match="No results in response"):
        transcript_processor.process_response({})

def test_process_response_no_alternatives(transcript_processor):
    """Test processing response with no alternatives."""
    response = {
        "results": {
            "file1": {
                "transcript": {
                    "results": [
                        {
                            "alternatives": []
                        }
                    ]
                }
            }
        }
    }
    
    result = transcript_processor.process_response(response)
    assert result["transcript"] == ""
    assert result["confidence"] == 0.0

def test_process_response_multiple_results(transcript_processor):
    """Test processing multiple results."""
    response = {
        "results": {
            "file1": {
                "transcript": {
                    "results": [
                        {
                            "alternatives": [
                                {
                                    "transcript": "First segment.",
                                    "confidence": 0.9
                                }
                            ]
                        },
                        {
                            "alternatives": [
                                {
                                    "transcript": "Second segment.",
                                    "confidence": 0.95
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    
    result = transcript_processor.process_response(response)
    assert "First segment. Second segment." in result["transcript"]
    assert result["confidence"] == 0.95  # Should take highest confidence

def test_recognition_with_custom_config(speech_recognizer):
    """Test recognition with custom configuration."""
    config = speech_recognizer.create_recognition_config("test.wav")
    
    # Test custom features
    assert config.features.enable_automatic_punctuation
    assert config.features.enable_word_time_offsets
    assert config.features.enable_word_confidence
    assert config.features.enable_spoken_punctuation
    assert config.features.enable_spoken_emojis

def test_error_handling(speech_recognizer, transcript_processor):
    """Test error handling in transcription process."""
    # Test invalid response format
    with pytest.raises(TranscriptionError):
        transcript_processor.process_response({"invalid": "format"})
    
    # Test missing required fields
    with pytest.raises(TranscriptionError):
        transcript_processor.process_response({
            "results": {
                "file1": {
                    "transcript": {
                        "results": [{}]
                    }
                }
            }
        }) 