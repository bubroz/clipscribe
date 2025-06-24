"""Unit tests for the transcriber module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil

from clipscribe.retrievers.transcriber import GeminiTranscriber
from clipscribe.models import VideoTranscript
from tests.fixtures import (
    get_mock_transcript, get_mock_gemini_response,
    create_test_audio_file, TEST_AUDIO_PATH
)


class TestGeminiTranscriber:
    """Test Gemini transcriber functionality."""
    
    @pytest.fixture
    def transcriber(self):
        """Create transcriber instance with test API key."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-api-key'}):
            return GeminiTranscriber()
    
    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary audio file for testing."""
        temp_dir = tempfile.mkdtemp()
        audio_path = Path(temp_dir) / "test_audio.wav"
        create_test_audio_file(audio_path, duration_seconds=3.0)
        yield audio_path
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-api-key'}):
            transcriber = GeminiTranscriber()
            assert transcriber.api_key == 'test-api-key'
            assert transcriber.client is not None
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                GeminiTranscriber()
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, transcriber, temp_audio_file):
        """Test successful audio transcription."""
        mock_response = Mock()
        mock_response.text = "Hello, this is a test video. We are testing ClipScribe transcription."
        
        with patch.object(transcriber.client, 'generate_content_async', 
                         return_value=AsyncMock(return_value=mock_response)()):
            result = await transcriber.transcribe_audio(str(temp_audio_file))
            
            assert isinstance(result, VideoTranscript)
            assert result.full_text == mock_response.text
            assert result.language == "en"
            assert result.confidence >= 0.0
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_custom_prompt(self, transcriber, temp_audio_file):
        """Test transcription with custom prompt."""
        custom_prompt = "This is a technical presentation about AI."
        mock_response = Mock()
        mock_response.text = "Technical content about artificial intelligence."
        
        with patch.object(transcriber.client, 'generate_content_async',
                         return_value=AsyncMock(return_value=mock_response)()):
            result = await transcriber.transcribe_audio(
                str(temp_audio_file), 
                prompt=custom_prompt
            )
            
            assert result.full_text == mock_response.text
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self, transcriber):
        """Test transcription with non-existent file."""
        with pytest.raises(FileNotFoundError):
            await transcriber.transcribe_audio("/non/existent/file.wav")
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, transcriber, temp_audio_file):
        """Test handling of API errors."""
        with patch.object(transcriber.client, 'generate_content_async',
                         side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                await transcriber.transcribe_audio(str(temp_audio_file))
    
    def test_validate_audio_file_size(self, transcriber):
        """Test audio file size validation."""
        # Create a mock file path
        mock_path = Mock()
        mock_path.stat.return_value.st_size = 100 * 1024 * 1024  # 100MB
        
        # Should not raise for 100MB file
        transcriber._validate_audio_file(mock_path)
        
        # Should raise for >100MB file
        mock_path.stat.return_value.st_size = 101 * 1024 * 1024  # 101MB
        with pytest.raises(ValueError, match="exceeds.*100MB"):
            transcriber._validate_audio_file(mock_path)
    
    @pytest.mark.asyncio
    async def test_transcribe_with_retry(self, transcriber, temp_audio_file):
        """Test retry logic for rate limits."""
        mock_response = Mock()
        mock_response.text = "Success after retry"
        
        # First call fails with rate limit, second succeeds
        with patch.object(transcriber.client, 'generate_content_async',
                         side_effect=[
                             Exception("Resource exhausted: Rate limit"),
                             AsyncMock(return_value=mock_response)()
                         ]):
            result = await transcriber.transcribe_audio(
                str(temp_audio_file),
                retry_on_rate_limit=True
            )
            
            assert result.full_text == "Success after retry"
    
    def test_calculate_cost(self, transcriber):
        """Test cost calculation for transcription."""
        # Test with 60 seconds (1 minute)
        cost = transcriber.calculate_cost(60)
        assert cost == 0.002  # $0.002 per minute
        
        # Test with 3600 seconds (1 hour)
        cost = transcriber.calculate_cost(3600)
        assert cost == 0.12  # $0.12 per hour
        
        # Test with fractional minutes
        cost = transcriber.calculate_cost(90)  # 1.5 minutes
        assert cost == 0.003  # $0.002 * 1.5
    
    def test_format_segments(self, transcriber):
        """Test segment formatting for subtitles."""
        segments = [
            {"start": 0.0, "end": 2.0, "text": "Hello"},
            {"start": 2.0, "end": 5.0, "text": "World"}
        ]
        
        # Test SRT format
        srt = transcriber.format_as_srt(segments)
        assert "1\n00:00:00,000 --> 00:00:02,000\nHello" in srt
        assert "2\n00:00:02,000 --> 00:00:05,000\nWorld" in srt
        
        # Test VTT format
        vtt = transcriber.format_as_vtt(segments)
        assert "WEBVTT" in vtt
        assert "00:00:00.000 --> 00:00:02.000\nHello" in vtt
    
    @pytest.mark.asyncio
    async def test_transcribe_with_language_detection(self, transcriber, temp_audio_file):
        """Test language detection in transcription."""
        mock_response = Mock()
        mock_response.text = "Bonjour, ceci est un test."
        
        with patch.object(transcriber.client, 'generate_content_async',
                         return_value=AsyncMock(return_value=mock_response)()):
            with patch.object(transcriber, 'detect_language', return_value='fr'):
                result = await transcriber.transcribe_audio(str(temp_audio_file))
                
                assert result.language == 'fr'
                assert result.full_text == mock_response.text


class TestTranscriberHelpers:
    """Test helper functions in transcriber module."""
    
    def test_time_to_srt_format(self):
        """Test time conversion to SRT format."""
        from clipscribe.retrievers.transcriber import time_to_srt_format
        
        assert time_to_srt_format(0.0) == "00:00:00,000"
        assert time_to_srt_format(61.5) == "00:01:01,500"
        assert time_to_srt_format(3661.123) == "01:01:01,123"
    
    def test_time_to_vtt_format(self):
        """Test time conversion to WebVTT format."""
        from clipscribe.retrievers.transcriber import time_to_vtt_format
        
        assert time_to_vtt_format(0.0) == "00:00:00.000"
        assert time_to_vtt_format(61.5) == "00:01:01.500"
        assert time_to_vtt_format(3661.123) == "01:01:01.123"  # :-) 