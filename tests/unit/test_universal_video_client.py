"""Unit tests for the universal video client."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil

from clipscribe.retrievers.universal_video_client import UniversalVideoClient
from clipscribe.models import VideoMetadata, VideoIntelligence
from tests.fixtures import (
    get_mock_video_metadata, get_mock_yt_dlp_info,
    get_mock_transcript, create_test_audio_file
)


class TestUniversalVideoClient:
    """Test universal video client functionality."""
    
    @pytest.fixture
    def client(self):
        """Create universal video client instance."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-api-key'}):
            return UniversalVideoClient()
    
    @pytest.fixture
    def mock_ydl(self):
        """Create mock yt-dlp instance."""
        mock = Mock()
        mock.extract_info.return_value = get_mock_yt_dlp_info()
        mock.download.return_value = None
        return mock
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for downloads."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_is_supported_url(self, client):
        """Test URL support detection."""
        # YouTube URLs
        assert client.is_supported_url("https://www.youtube.com/watch?v=test")
        assert client.is_supported_url("https://youtu.be/test")
        
        # Other platforms
        assert client.is_supported_url("https://vimeo.com/123456")
        assert client.is_supported_url("https://twitter.com/user/status/123")
        assert client.is_supported_url("https://www.tiktok.com/@user/video/123")
        
        # Invalid URLs
        assert not client.is_supported_url("not-a-url")
        assert not client.is_supported_url("https://example.com/page")
    
    @pytest.mark.asyncio
    async def test_extract_video_info_success(self, client, mock_ydl):
        """Test successful video info extraction."""
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            info = await client.extract_video_info("https://youtube.com/watch?v=test")
            
            assert info['id'] == "dQw4w9WgXcQ"
            assert info['title'] == "Test Video - ClipScribe Demo"
            assert info['duration'] == 180
    
    @pytest.mark.asyncio
    async def test_extract_video_info_error(self, client):
        """Test handling of extraction errors."""
        mock_ydl = Mock()
        mock_ydl.extract_info.side_effect = Exception("Extraction failed")
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with pytest.raises(Exception, match="Extraction failed"):
                await client.extract_video_info("https://youtube.com/watch?v=test")
    
    @pytest.mark.asyncio
    async def test_download_audio_success(self, client, mock_ydl, temp_dir):
        """Test successful audio download."""
        # Mock the download process
        def mock_download(urls):
            # Create a dummy audio file
            audio_path = Path(temp_dir) / "test_video.m4a"
            create_test_audio_file(audio_path)
            return None
        
        mock_ydl.download = mock_download
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            audio_path = await client.download_audio(
                "https://youtube.com/watch?v=test",
                output_dir=temp_dir
            )
            
            assert audio_path.exists()
            assert audio_path.suffix in ['.m4a', '.mp3', '.wav']
    
    def test_build_ydl_options(self, client):
        """Test yt-dlp options building."""
        options = client._build_ydl_options(output_dir="/tmp", quiet=True)
        
        assert options['quiet'] is True
        assert options['format'] == 'bestaudio/best'
        assert 'outtmpl' in options
        assert options['postprocessors'][0]['preferredcodec'] == 'm4a'
    
    def test_platform_specific_options(self, client):
        """Test platform-specific option configuration."""
        # Twitter options
        twitter_opts = client._get_platform_options("https://twitter.com/user/status/123")
        assert 'http_headers' in twitter_opts
        
        # TikTok options
        tiktok_opts = client._get_platform_options("https://www.tiktok.com/@user/video/123")
        assert 'http_headers' in tiktok_opts
        assert 'User-Agent' in tiktok_opts['http_headers']
    
    @pytest.mark.asyncio
    async def test_get_video_metadata(self, client):
        """Test metadata extraction from yt-dlp info."""
        info = get_mock_yt_dlp_info()
        metadata = await client._extract_metadata(info)
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.video_id == "dQw4w9WgXcQ"
        assert metadata.title == "Test Video - ClipScribe Demo"
        assert metadata.duration == 180
    
    @pytest.mark.asyncio
    async def test_full_transcription_flow(self, client, mock_ydl, temp_dir):
        """Test complete transcription workflow."""
        # Mock audio download
        def mock_download(urls):
            audio_path = Path(temp_dir) / "test_video.m4a"
            create_test_audio_file(audio_path)
            return None
        
        mock_ydl.download = mock_download
        
        # Mock transcriber
        mock_transcript = get_mock_transcript()
        mock_transcriber = Mock()
        mock_transcriber.transcribe_audio = AsyncMock(return_value=mock_transcript)
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with patch.object(client, 'transcriber', mock_transcriber):
                result = await client.transcribe_video(
                    "https://youtube.com/watch?v=test",
                    output_dir=temp_dir
                )
                
                assert isinstance(result, VideoIntelligence)
                assert result.transcript.full_text == mock_transcript.full_text
                assert result.metadata.video_id == "dQw4w9WgXcQ"
    
    def test_retry_mechanism(self, client):
        """Test retry logic for failed downloads."""
        attempts = []
        
        def mock_download_with_retry(urls):
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("Network error")
            return None
        
        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = get_mock_yt_dlp_info()
        mock_ydl.download = mock_download_with_retry
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            # Should succeed after retries
            client._download_with_retry(mock_ydl, "https://youtube.com/watch?v=test")
            assert len(attempts) == 3
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self, client, temp_dir):
        """Test temporary file cleanup."""
        # Create some temp files
        temp_file1 = Path(temp_dir) / "temp1.m4a"
        temp_file2 = Path(temp_dir) / "temp2.part"
        temp_file1.touch()
        temp_file2.touch()
        
        # Run cleanup
        await client._cleanup_temp_files(temp_dir)
        
        # Check that .part files are removed
        assert not temp_file2.exists()
        assert temp_file1.exists()  # Non-.part files should remain
    
    def test_sanitize_filename(self, client):
        """Test filename sanitization."""
        # Test with special characters
        filename = client._sanitize_filename("Test: Video / With \\ Special * Chars?")
        assert ":" not in filename
        assert "/" not in filename
        assert "\\" not in filename
        assert "*" not in filename
        assert "?" not in filename
    
    @pytest.mark.asyncio
    async def test_cookie_authentication(self, client, mock_ydl):
        """Test using cookies for authentication."""
        cookie_file = "/tmp/cookies.txt"
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with patch.object(client, '_build_ydl_options') as mock_options:
                await client.extract_video_info(
                    "https://youtube.com/watch?v=test",
                    cookies_file=cookie_file
                )
                
                # Check that cookie file was added to options
                mock_options.assert_called()
                call_args = mock_options.call_args
                assert any('cookiefile' in str(arg) for arg in call_args)
    
    def test_format_duration(self, client):
        """Test duration formatting."""
        assert client._format_duration(0) == "0:00"
        assert client._format_duration(59) == "0:59"
        assert client._format_duration(60) == "1:00"
        assert client._format_duration(3661) == "1:01:01"
    
    @pytest.mark.asyncio
    async def test_parallel_download(self, client):
        """Test parallel video processing."""
        urls = [
            "https://youtube.com/watch?v=1",
            "https://youtube.com/watch?v=2",
            "https://youtube.com/watch?v=3"
        ]
        
        mock_results = []
        for i, url in enumerate(urls):
            mock_result = Mock()
            mock_result.metadata.video_id = str(i + 1)
            mock_results.append(mock_result)
        
        with patch.object(client, 'transcribe_video', 
                         side_effect=mock_results):
            results = await client.transcribe_multiple(urls)
            
            assert len(results) == 3
            assert all(r.metadata.video_id in ['1', '2', '3'] for r in results)  # :-) 