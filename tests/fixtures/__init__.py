"""Test fixtures for ClipScribe tests."""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from clipscribe.models import (
    VideoMetadata, VideoTranscript, VideoChapter,
    KeyPoint, Entity, VideoIntelligence
)

# Base directory for test fixtures
FIXTURES_DIR = Path(__file__).parent

def get_mock_video_metadata() -> VideoMetadata:
    """Get mock video metadata for testing."""
    return VideoMetadata(
        video_id="dQw4w9WgXcQ",
        title="Test Video - ClipScribe Demo",
        channel="Test Channel",
        channel_id="UC_test_channel",
        duration=180,  # 3 minutes
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        published_at=datetime(2024, 1, 1, 12, 0, 0),
        view_count=1000000,
        description="This is a test video for ClipScribe",
        tags=["test", "demo", "clipscribe"]
    )

def get_mock_transcript() -> VideoTranscript:
    """Get mock transcript for testing."""
    return VideoTranscript(
        full_text="Hello, this is a test video. We are testing ClipScribe transcription. It works great!",
        segments=[
            {"start": 0.0, "end": 2.0, "text": "Hello, this is a test video."},
            {"start": 2.0, "end": 5.0, "text": "We are testing ClipScribe transcription."},
            {"start": 5.0, "end": 7.0, "text": "It works great!"}
        ],
        language="en",
        confidence=0.95
    )

def get_mock_video_intelligence() -> VideoIntelligence:
    """Get complete mock video intelligence for testing."""
    return VideoIntelligence(
        metadata=get_mock_video_metadata(),
        transcript=get_mock_transcript(),
        chapters=[
            VideoChapter(
                start_time=0,
                end_time=60,
                title="Introduction",
                summary="Introduction to the test video"
            ),
            VideoChapter(
                start_time=60,
                end_time=180,
                title="Main Content",
                summary="Main content of the test"
            )
        ],
        key_points=[
            KeyPoint(
                timestamp=2,
                text="ClipScribe is being tested",
                importance=0.9,
                context="Testing the transcription functionality"
            )
        ],
        summary="This is a test video demonstrating ClipScribe's transcription capabilities.",
        entities=[
            Entity(
                name="ClipScribe",
                type="TECHNOLOGY",
                properties={"description": "AI-powered video transcription tool"},
                confidence=0.95,
                timestamp=3
            )
        ],
        topics=["testing", "transcription", "AI"],
        sentiment={"positive": 0.8, "neutral": 0.2, "negative": 0.0},
        confidence_score=0.95,
        processing_cost=0.001,
        processing_time=2.5
    )

def get_mock_gemini_response() -> Dict[str, Any]:
    """Get mock Gemini API response for testing."""
    return {
        "text": "Hello, this is a test video. We are testing ClipScribe transcription. It works great!",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "Hello, this is a test video."},
            {"start": 2.0, "end": 5.0, "text": "We are testing ClipScribe transcription."},
            {"start": 5.0, "end": 7.0, "text": "It works great!"}
        ]
    }

def get_mock_yt_dlp_info() -> Dict[str, Any]:
    """Get mock yt-dlp info dict for testing."""
    return {
        "id": "dQw4w9WgXcQ",
        "title": "Test Video - ClipScribe Demo",
        "uploader": "Test Channel",
        "uploader_id": "UC_test_channel",
        "duration": 180,
        "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "upload_date": "20240101",
        "view_count": 1000000,
        "description": "This is a test video for ClipScribe",
        "tags": ["test", "demo", "clipscribe"],
        "formats": [
            {
                "format_id": "140",
                "ext": "m4a",
                "acodec": "mp4a.40.2",
                "abr": 128,
                "url": "https://example.com/audio.m4a"
            }
        ]
    }

# Audio test helpers
def create_test_audio_file(path: Path, duration_seconds: float = 3.0) -> None:
    """Create a silent audio file for testing.
    
    Note: This creates a simple WAV file with silence.
    For real tests, you might want to use pre-recorded samples.
    """
    import wave
    import array
    
    sample_rate = 44100
    num_samples = int(sample_rate * duration_seconds)
    
    # Create silence (zeros)
    audio_data = array.array('h', [0] * num_samples)
    
    with wave.open(str(path), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

# Path to test assets
TEST_AUDIO_PATH = FIXTURES_DIR / "test_audio.wav"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Example SRT content for testing
TEST_SRT_CONTENT = """1
00:00:00,000 --> 00:00:02,000
Hello, this is a test video.

2
00:00:02,000 --> 00:00:05,000
We are testing ClipScribe transcription.

3
00:00:05,000 --> 00:00:07,000
It works great!
"""

# Example WebVTT content for testing
TEST_VTT_CONTENT = """WEBVTT

00:00:00.000 --> 00:00:02.000
Hello, this is a test video.

00:00:02.000 --> 00:00:05.000
We are testing ClipScribe transcription.

00:00:05.000 --> 00:00:07.000
It works great!
"""  # :-) 