# tests/unit/test_universal_video_client.py
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
from clipscribe.models import VideoMetadata
import asyncio
import yt_dlp

@pytest.fixture
def client():
    """Fixture to create an EnhancedUniversalVideoClient instance."""
    return EnhancedUniversalVideoClient()

def test_initialization(client):
    """Test that the client initializes with the correct options."""
    assert client is not None
    assert 'writesubtitles' in client.temporal_opts
    assert client.temporal_opts['sponsorblock_mark'] == 'all'

@patch('yt_dlp.YoutubeDL')
def test_is_supported_url_success(mock_yt_dlp, client):
    """Test that is_supported_url returns True for a valid URL."""
    mock_instance = mock_yt_dlp.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = {}  # Simulate success
    
    assert client.is_supported_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    mock_instance.extract_info.assert_called_with("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=False, process=False)

@patch('yt_dlp.YoutubeDL')
def test_is_supported_url_failure(mock_yt_dlp, client):
    """Test that is_supported_url returns False for an invalid URL."""
    mock_instance = mock_yt_dlp.return_value.__enter__.return_value
    mock_instance.extract_info.side_effect = yt_dlp.utils.DownloadError("Unsupported URL")
    
    assert client.is_supported_url("http://unsupported.url/video") is False

@pytest.mark.asyncio
async def test_get_video_info(client):
    """Test fetching video metadata."""
    mock_info = {
        'id': 'dQw4w9WgXcQ',
        'title': 'Test Video',
        'uploader': 'Test Channel',
        'duration': 212,
        'webpage_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'upload_date': '20091025',
        'view_count': 1000000,
        'description': 'A test video.',
        'tags': ['test', 'video'],
        'extractor': 'youtube'
    }
    with patch('yt_dlp.YoutubeDL') as mock_yt_dlp:
        mock_instance = mock_yt_dlp.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = mock_info
        
        metadata = await client.get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.title == "Test Video"
        assert metadata.duration == 212
        assert metadata.channel == "Test Channel"

@pytest.mark.asyncio
async def test_download_audio(client):
    """Test downloading audio from a URL."""
    mock_info = {
        'id': 'dQw4w9WgXcQ',
        'title': 'Test Audio',
        'duration': 212,
        'extractor': 'youtube'
    }
    with patch('yt_dlp.YoutubeDL') as mock_yt_dlp:
        mock_instance = mock_yt_dlp.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = mock_info
        
        # Mock the file system to avoid actual downloads
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=['Test Audio-dQw4w9WgXcQ.mp3']):
            
            audio_path, metadata = await client.download_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ", output_dir="/tmp/test")
            
            assert "Test Audio-dQw4w9WgXcQ.mp3" in audio_path
            assert metadata.title == "Test Audio"
            # Check that download was called
            mock_instance.download.assert_called_with(["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
