"""Unit tests for video_transcriber.py module."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from clipscribe.retrievers.video_transcriber import VideoTranscriber
from clipscribe.models import VideoTranscript, VideoMetadata

# DEPRECATED: Skip all tests in this file
pytest.skip("These tests are deprecated - VideoTranscriber has been replaced by Voxtral-Grok pipeline", allow_module_level=True)


@pytest.fixture
def video_transcriber():
    """Create a VideoTranscriber instance for testing."""
    return VideoTranscriber(use_pro=True)


@pytest.fixture
def mock_video_metadata():
    """Create mock video metadata."""
    from datetime import datetime
    return VideoMetadata(
        video_id="test_123",
        url="https://www.youtube.com/watch?v=test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="test_channel",
        published_at=datetime.now(),
        duration=300,
        view_count=1000,
        description="Test description",
        tags=["test"]
    )


@pytest.fixture
def mock_transcription_analysis():
    """Create mock transcription analysis response."""
    return {
        "transcript": "This is a test transcript for testing purposes.",
        "language": "en",
        "confidence_score": 0.95,
        "processing_cost": 0.15,
        "summary": "A test transcript summary.",
        "key_points": [
            {"text": "Test key point 1", "importance": 0.8},
            {"text": "Test key point 2", "importance": 0.6}
        ],
        "entities": [
            {"name": "Test Entity", "type": "PERSON", "confidence": 0.9}
        ],
        "relationships": [
            {
                "subject": "Test Entity",
                "predicate": "works_at",
                "object": "Test Company",
                "confidence": 0.85
            }
        ],
        "topics": ["technology", "testing"]
    }


class TestVideoTranscriber:
    """Test cases for VideoTranscriber class."""

    def test_init_with_pro(self):
        """Test VideoTranscriber initialization with Pro model."""
        transcriber = VideoTranscriber(use_pro=True)
        assert transcriber.use_pro is True
        assert hasattr(transcriber, 'transcriber')

    def test_init_with_flash(self):
        """Test VideoTranscriber initialization with Flash model."""
        transcriber = VideoTranscriber(use_pro=False)
        assert transcriber.use_pro is False

    def test_init_with_performance_monitor(self):
        """Test VideoTranscriber initialization with performance monitor."""
        mock_monitor = MagicMock()
        transcriber = VideoTranscriber(use_pro=True, performance_monitor=mock_monitor)
        assert transcriber.performance_monitor == mock_monitor

    @pytest.mark.asyncio
    async def test_transcribe_video_success(self, video_transcriber, mock_video_metadata, mock_transcription_analysis):
        """Test successful video transcription."""
        with patch.object(video_transcriber.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = mock_transcription_analysis

            result = await video_transcriber.transcribe_video(
                media_file="test_video.mp4",
                metadata=mock_video_metadata,
                duration=300
            )

            assert result == mock_transcription_analysis
            mock_transcribe.assert_called_once_with(
                "test_video.mp4", mock_video_metadata, 300
            )

    @pytest.mark.asyncio
    async def test_transcribe_video_error_handling(self, video_transcriber, mock_video_metadata):
        """Test error handling during transcription."""
        with patch.object(video_transcriber.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.side_effect = Exception("Transcription failed")

            with pytest.raises(Exception, match="Transcription failed"):
                await video_transcriber.transcribe_video(
                    media_file="test_video.mp4",
                    metadata=mock_video_metadata,
                    duration=300
                )

    def test_create_transcript_object(self, video_transcriber, mock_transcription_analysis):
        """Test creation of VideoTranscript object from analysis."""
        transcript = video_transcriber.create_transcript_object(
            mock_transcription_analysis, 300
        )

        assert isinstance(transcript, VideoTranscript)
        assert transcript.full_text == "This is a test transcript for testing purposes."
        assert transcript.language == "en"
        assert transcript.language == "en"
        assert len(transcript.segments) > 0

    def test_generate_segments_basic(self, video_transcriber):
        """Test basic segment generation."""
        text = "This is a test transcript."
        duration = 30

        segments = video_transcriber._generate_segments(text, duration)

        assert len(segments) == 1
        assert segments[0]["text"] == "This is a test transcript."
        assert segments[0]["start"] == 0
        assert segments[0]["end"] == 30

    def test_generate_segments_multiple_words(self, video_transcriber):
        """Test segment generation with multiple words."""
        text = "This is a test transcript with multiple words for testing purposes."
        duration = 60

        segments = video_transcriber._generate_segments(text, duration, segment_length=30)

        # The algorithm creates segments based on word distribution, resulting in 3 segments
        assert len(segments) == 3
        assert segments[0]["start"] == 0
        assert segments[-1]["end"] == 60

    def test_generate_segments_empty_text(self, video_transcriber):
        """Test segment generation with empty text."""
        segments = video_transcriber._generate_segments("", 30)

        assert segments == []

    def test_generate_segments_no_words(self, video_transcriber):
        """Test segment generation with whitespace only."""
        segments = video_transcriber._generate_segments("   \n\t   ", 30)

        assert segments == []

    def test_get_transcription_cost(self, video_transcriber, mock_transcription_analysis):
        """Test transcription cost extraction."""
        cost = video_transcriber.get_transcription_cost(mock_transcription_analysis)

        assert cost == 0.15

    def test_get_transcription_cost_missing(self, video_transcriber):
        """Test transcription cost extraction when missing."""
        analysis = {"transcript": "test", "language": "en"}
        cost = video_transcriber.get_transcription_cost(analysis)

        assert cost == 0.0

    def test_get_transcription_cost_none(self, video_transcriber):
        """Test transcription cost extraction with None."""
        cost = video_transcriber.get_transcription_cost(None)

        assert cost == 0.0

    @pytest.mark.asyncio
    async def test_large_video_handling(self, video_transcriber, mock_video_metadata, mock_transcription_analysis):
        """Test handling of large video files."""
        # Mock a large video scenario
        mock_transcription_analysis["transcript"] = "Large transcript content " * 1000

        with patch.object(video_transcriber.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = mock_transcription_analysis

            result = await video_transcriber.transcribe_video(
                media_file="large_video.mp4",
                metadata=mock_video_metadata,
                duration=3600  # 1 hour video
            )

            assert result == mock_transcription_analysis
            assert "Large transcript content" in result["transcript"]

    def test_segment_generation_with_long_text(self, video_transcriber):
        """Test segment generation with long transcript."""
        long_text = " ".join([f"word{i}" for i in range(1000)])
        duration = 300

        segments = video_transcriber._generate_segments(long_text, duration, segment_length=30)

        # Should create multiple segments
        assert len(segments) > 1
        assert all("word" in segment["text"] for segment in segments)

        # Verify timing is correct
        for i, segment in enumerate(segments[:-1]):
            assert segment["end"] == segments[i + 1]["start"]

        # Last segment should end at video duration
        assert segments[-1]["end"] == duration

    def test_segment_generation_edge_case_single_word(self, video_transcriber):
        """Test segment generation with single word."""
        segments = video_transcriber._generate_segments("Hello", 10)

        assert len(segments) == 1
        assert segments[0]["text"] == "Hello"
        assert segments[0]["start"] == 0
        assert segments[0]["end"] == 10

    def test_segment_generation_very_short_video(self, video_transcriber):
        """Test segment generation with very short video."""
        text = "This is a short video transcript."
        duration = 5

        segments = video_transcriber._generate_segments(text, duration)

        assert len(segments) == 1
        assert segments[0]["end"] == 5

    def test_transcriber_initialization_pro(self, video_transcriber):
        """Test that GeminiFlashTranscriber is initialized with pro=True."""
        assert hasattr(video_transcriber, 'transcriber')
        # Verify the transcriber was created with the correct parameters
        assert video_transcriber.use_pro is True

    def test_transcriber_initialization_flash(self):
        """Test that GeminiFlashTranscriber is initialized with pro=False."""
        transcriber = VideoTranscriber(use_pro=False)
        assert transcriber.use_pro is False

    @pytest.mark.asyncio
    async def test_concurrent_transcriptions(self, video_transcriber, mock_video_metadata, mock_transcription_analysis):
        """Test concurrent transcription operations."""
        import asyncio

        with patch.object(video_transcriber.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe:
            mock_transcribe.return_value = mock_transcription_analysis

            # Simulate multiple concurrent transcriptions
            tasks = [
                video_transcriber.transcribe_video(
                    media_file=f"video{i}.mp4",
                    metadata=mock_video_metadata,
                    duration=300
                )
                for i in range(3)
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            assert mock_transcribe.call_count == 3

    def test_create_transcript_object_with_none_analysis(self, video_transcriber):
        """Test creating transcript object with None analysis."""
        transcript = video_transcriber.create_transcript_object(None, 300)

        assert isinstance(transcript, VideoTranscript)
        assert transcript.full_text == ""
        assert transcript.language == "en"
        assert transcript.language == "en"

    def test_create_transcript_object_missing_fields(self, video_transcriber):
        """Test creating transcript object with missing fields in analysis."""
        analysis = {
            "transcript": "Test transcript",
            # Missing language field
        }

        transcript = video_transcriber.create_transcript_object(analysis, 300)

        assert transcript.full_text == "Test transcript"
        assert transcript.language == "en"  # Default value

    def test_performance_monitor_integration(self):
        """Test integration with performance monitor."""
        mock_monitor = MagicMock()
        transcriber = VideoTranscriber(use_pro=True, performance_monitor=mock_monitor)

        assert transcriber.performance_monitor == mock_monitor

    @pytest.mark.asyncio
    async def test_transcribe_video_analysis_error(self, video_transcriber, mock_video_metadata):
        """Test transcribe_video with analysis error."""
        with patch.object(video_transcriber.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe:
            # Mock analysis with error
            mock_transcribe.return_value = {"error": "API temporarily unavailable"}

            with pytest.raises(Exception, match="Transcription failed: API temporarily unavailable"):
                await video_transcriber.transcribe_video("test_video.mp4", mock_video_metadata, 300)
