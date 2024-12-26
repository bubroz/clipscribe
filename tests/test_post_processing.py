"""Tests for post-processing functionality."""

import os
import pytest
from unittest.mock import Mock, patch
import google.generativeai as genai
from src.post_processing_gemini import GeminiPostProcessor, ClipSuggestion, ProcessingError

@pytest.fixture
def post_processor():
    """Fixture for GeminiPostProcessor instance."""
    with patch('google.generativeai.GenerativeModel') as mock_model:
        processor = GeminiPostProcessor()
        processor.gemini_model = mock_model
        yield processor

@pytest.fixture
def mock_transcript_data():
    """Fixture for mock transcript data."""
    return {
        "transcript": "This is a test transcript about artificial intelligence and machine learning.",
        "confidence": 0.95,
        "words": [
            {
                "word": "This",
                "startOffset": "0.0s",
                "endOffset": "0.4s",
                "confidence": 0.96
            },
            {
                "word": "is",
                "startOffset": "0.4s",
                "endOffset": "0.6s",
                "confidence": 0.97
            }
        ],
        "language_code": "en-US"
    }

@pytest.fixture
def mock_youtube_metadata():
    """Fixture for mock YouTube metadata."""
    return {
        "title": "Test Video",
        "author": "Test Channel",
        "url": "https://www.youtube.com/watch?v=test",
        "publish_date": "20240101",
        "views": 1000,
        "duration": 120,
        "description": "This is a test video about AI and ML."
    }

def test_process_transcript(post_processor, mock_transcript_data, mock_youtube_metadata):
    """Test transcript processing."""
    # Mock Gemini response
    mock_response = Mock()
    mock_response.text = '{"summary": "Test summary", "topics": ["AI", "ML"]}'
    post_processor.gemini_model.generate_content.return_value = mock_response
    
    result = post_processor.process_transcript(
        mock_transcript_data,
        mock_youtube_metadata.get("description", ""),
        mock_youtube_metadata
    )
    
    assert isinstance(result, dict)
    assert "metadata" in result
    assert "summary" in result
    assert "segments" in result
    assert "transcript_analysis" in result

def test_refine_transcript(post_processor):
    """Test transcript refinement."""
    test_transcript = "um, this is like, you know, a test transcript"
    mock_response = Mock()
    mock_response.text = "This is a test transcript."
    post_processor.gemini_model.generate_content.return_value = mock_response
    
    refined = post_processor.refine_transcript(test_transcript)
    assert isinstance(refined, str)
    assert "um" not in refined.lower()
    assert "like" not in refined.lower()
    assert "you know" not in refined.lower()

def test_create_clip(post_processor, tmp_path):
    """Test clip creation."""
    # Create a temporary video file
    video_path = tmp_path / "test.mp4"
    with open(video_path, "wb") as f:
        f.write(b"test video content")
    
    suggestion = ClipSuggestion(
        text="Test segment",
        start_time=0.0,
        end_time=5.0,
        confidence=0.9,
        explanation="Test explanation",
        topic="test_topic"
    )
    
    with patch('moviepy.editor.VideoFileClip') as mock_video:
        mock_video.return_value.duration = 10.0
        mock_video.return_value.audio = None
        
        clip_path = post_processor.create_clip(str(video_path), suggestion)
        assert isinstance(clip_path, str)
        assert "test_topic" in clip_path

def test_analyze_sentiment(post_processor, mock_transcript_data):
    """Test sentiment analysis."""
    mock_response = Mock()
    mock_response.text = "0.8"  # Positive sentiment
    post_processor.gemini_model.generate_content.return_value = mock_response
    
    segments = post_processor._analyze_sentiment_over_time({"segments": [mock_transcript_data]})
    assert isinstance(segments, list)
    assert len(segments) > 0
    assert "sentiment_score" in segments[0]
    assert isinstance(segments[0]["sentiment_score"], float)

def test_analyze_topics(post_processor, mock_transcript_data):
    """Test topic analysis."""
    mock_response = Mock()
    mock_response.text = '[{"topic": "AI", "percentage": 60, "confidence": 0.9}]'
    post_processor.gemini_model.generate_content.return_value = mock_response
    
    topics = post_processor._analyze_topic_distribution(
        mock_transcript_data["transcript"],
        {"title": "Test", "author": "Test"}
    )
    assert isinstance(topics, list)
    assert len(topics) > 0
    assert "topic" in topics[0]
    assert "percentage" in topics[0]
    assert "confidence" in topics[0]

def test_error_handling(post_processor):
    """Test error handling in post-processing."""
    # Test invalid transcript
    with pytest.raises(ValueError):
        post_processor.refine_transcript(None)
    
    # Test processing error
    post_processor.gemini_model.generate_content.side_effect = Exception("API Error")
    with pytest.raises(ProcessingError):
        post_processor.process_transcript({}, "", {})

def test_create_logical_segments(post_processor, mock_transcript_data):
    """Test logical segment creation."""
    mock_response = Mock()
    mock_response.text = '[{"text": "Test segment", "topic": "AI", "impact_score": 0.9, "context": "Test context"}]'
    post_processor.gemini_model.generate_content.return_value = mock_response
    
    segments = post_processor.create_logical_segments(mock_transcript_data)
    assert isinstance(segments, list)
    for segment in segments:
        assert "text" in segment
        assert "topic" in segment
        assert "impact_score" in segment
        assert "context" in segment

def test_search_transcript_segments(post_processor, mock_transcript_data):
    """Test transcript segment search."""
    mock_response = Mock()
    mock_response.text = '[{"index": 0, "confidence": 0.9, "explanation": "Test", "topic": "AI"}]'
    post_processor.gemini_model.generate_content.return_value = mock_response
    
    suggestions = post_processor.search_transcript_segments("AI", mock_transcript_data)
    assert isinstance(suggestions, list)
    for suggestion in suggestions:
        assert isinstance(suggestion, ClipSuggestion)
        assert suggestion.confidence >= 0.0
        assert suggestion.confidence <= 1.0
        assert isinstance(suggestion.text, str)
        assert isinstance(suggestion.explanation, str) 