"""Tests for YouTube downloading functionality."""

import os
import pytest
from unittest.mock import Mock, patch
from src.transcription import YouTubeDownloader
from src.error_handling import YouTubeDownloadError

# Test constants
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=eIho2S0ZahI"
INVALID_URL = "https://www.youtube.com/watch?v=invalid"

@pytest.fixture
def youtube_downloader():
    """Fixture for YouTubeDownloader instance."""
    return YouTubeDownloader()

@pytest.fixture
def mock_yt_dlp():
    """Fixture for mocked yt_dlp."""
    with patch('yt_dlp.YoutubeDL') as mock:
        yield mock

def test_download_audio_success(youtube_downloader, mock_yt_dlp):
    """Test successful audio download."""
    # Mock successful download
    mock_info = {
        'title': 'Test Video',
        'uploader': 'Test Channel',
        'upload_date': '20240101',
        'view_count': 1000,
        'duration': 120
    }
    mock_yt_dlp.return_value.__enter__.return_value.extract_info.return_value = mock_info
    
    # Test download
    audio_file, audio_size, metadata, video_file, video_size = youtube_downloader.download_audio(
        TEST_VIDEO_URL,
        keep_video=False
    )
    
    assert os.path.exists(audio_file)
    assert metadata['title'] == 'test_video'
    assert metadata['duration'] == 120

def test_download_audio_invalid_url(youtube_downloader):
    """Test download with invalid URL."""
    with pytest.raises(YouTubeDownloadError):
        youtube_downloader.download_audio(INVALID_URL)

def test_download_with_video_quality(youtube_downloader, mock_yt_dlp):
    """Test download with specific video quality."""
    mock_info = {
        'title': 'Test Video',
        'uploader': 'Test Channel',
        'upload_date': '20240101',
        'view_count': 1000,
        'duration': 120
    }
    mock_yt_dlp.return_value.__enter__.return_value.extract_info.return_value = mock_info
    
    audio_file, audio_size, metadata, video_file, video_size = youtube_downloader.download_audio(
        TEST_VIDEO_URL,
        keep_video=True,
        video_quality='720p'
    )
    
    assert video_file is not None
    assert os.path.exists(video_file)

def test_download_audio_file_size_limit(youtube_downloader, mock_yt_dlp):
    """Test download with file size limit."""
    # Mock large file
    mock_info = {
        'title': 'Large Video',
        'duration': 7200  # 2 hours
    }
    mock_yt_dlp.return_value.__enter__.return_value.extract_info.return_value = mock_info
    
    with pytest.raises(YouTubeDownloadError, match="File size exceeds limit"):
        youtube_downloader.download_audio(TEST_VIDEO_URL)

def test_metadata_extraction(youtube_downloader, mock_yt_dlp):
    """Test metadata extraction."""
    mock_info = {
        'title': 'Test Video',
        'uploader': 'Test Channel',
        'upload_date': '20240101',
        'view_count': 1000,
        'duration': 120,
        'description': 'Test description'
    }
    mock_yt_dlp.return_value.__enter__.return_value.extract_info.return_value = mock_info
    
    audio_file, audio_size, metadata, video_file, video_size = youtube_downloader.download_audio(
        TEST_VIDEO_URL
    )
    
    assert metadata['title'] == 'test_video'
    assert metadata['author'] == 'Test Channel'
    assert metadata['views'] == 1000
    assert metadata['duration'] == 120 