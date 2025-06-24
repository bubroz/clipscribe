"""Integration tests for the complete ClipScribe workflow."""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
import tempfile
import shutil
import json

from clipscribe.retrievers.universal_video_client import UniversalVideoClient
from clipscribe.retrievers.youtube_client import YouTubeClient
from clipscribe.models import VideoIntelligence
from tests.fixtures import (
    get_mock_yt_dlp_info, get_mock_transcript,
    create_test_audio_file, TEST_VIDEO_URL
)


class TestFullWorkflow:
    """Test complete ClipScribe workflow from URL to transcript."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Setup test environment variables."""
        with patch.dict('os.environ', {
            'GOOGLE_API_KEY': 'test-api-key',
            'CLIPSCRIBE_OUTPUT_DIR': '/tmp/clipscribe-test'
        }):
            yield
    
    @pytest.mark.asyncio
    async def test_youtube_transcription_workflow(self, temp_output_dir):
        """Test complete YouTube video transcription."""
        # Mock yt-dlp download
        def mock_download(urls):
            audio_path = Path(temp_output_dir) / "test_video.m4a"
            create_test_audio_file(audio_path, duration_seconds=5.0)
            return None
        
        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = get_mock_yt_dlp_info()
        mock_ydl.download = mock_download
        
        # Mock Gemini transcription
        mock_transcript = get_mock_transcript()
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                # Setup mock response
                mock_response = Mock()
                mock_response.text = mock_transcript.full_text
                mock_model.return_value.generate_content_async = AsyncMock(
                    return_value=mock_response
                )
                
                # Run workflow
                client = UniversalVideoClient()
                result = await client.transcribe_video(
                    TEST_VIDEO_URL,
                    output_dir=temp_output_dir,
                    save_outputs=True
                )
                
                # Verify result
                assert isinstance(result, VideoIntelligence)
                assert result.metadata.video_id == "dQw4w9WgXcQ"
                assert result.transcript.full_text == mock_transcript.full_text
                
                # Check output files were created
                output_files = list(Path(temp_output_dir).glob("*"))
                assert any(f.suffix == '.json' for f in output_files)
                assert any(f.suffix == '.txt' for f in output_files)
    
    @pytest.mark.asyncio
    async def test_multi_platform_support(self):
        """Test transcription from different platforms."""
        platforms = [
            ("https://vimeo.com/123456", "vimeo"),
            ("https://twitter.com/user/status/123", "twitter"),
            ("https://www.tiktok.com/@user/video/123", "tiktok")
        ]
        
        client = UniversalVideoClient()
        
        for url, platform in platforms:
            # Mock platform-specific extraction
            mock_info = get_mock_yt_dlp_info()
            mock_info['extractor'] = platform
            
            with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
                mock_ydl = Mock()
                mock_ydl.extract_info.return_value = mock_info
                mock_ydl_class.return_value = mock_ydl
                
                info = await client.extract_video_info(url)
                assert info['extractor'] == platform
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling throughout the workflow."""
        client = UniversalVideoClient()
        
        # Test invalid URL
        with pytest.raises(ValueError, match="Unsupported URL"):
            await client.transcribe_video("https://invalid.com/page")
        
        # Test network error during download
        mock_ydl = Mock()
        mock_ydl.extract_info.side_effect = Exception("Network error")
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with pytest.raises(Exception, match="Network error"):
                await client.transcribe_video(TEST_VIDEO_URL)
        
        # Test API error during transcription
        mock_ydl.extract_info.side_effect = None
        mock_ydl.extract_info.return_value = get_mock_yt_dlp_info()
        mock_ydl.download.return_value = None
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_model.return_value.generate_content_async.side_effect = Exception(
                    "API quota exceeded"
                )
                
                with pytest.raises(Exception, match="API quota exceeded"):
                    await client.transcribe_video(TEST_VIDEO_URL)
    
    @pytest.mark.asyncio
    async def test_output_formats(self, temp_output_dir):
        """Test different output format generation."""
        # Setup mocks
        def mock_download(urls):
            audio_path = Path(temp_output_dir) / "test_video.m4a"
            create_test_audio_file(audio_path)
            return None
        
        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = get_mock_yt_dlp_info()
        mock_ydl.download = mock_download
        
        mock_transcript = get_mock_transcript()
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_response = Mock()
                mock_response.text = mock_transcript.full_text
                mock_model.return_value.generate_content_async = AsyncMock(
                    return_value=mock_response
                )
                
                client = UniversalVideoClient()
                result = await client.transcribe_video(
                    TEST_VIDEO_URL,
                    output_dir=temp_output_dir,
                    save_outputs=True,
                    output_formats=['txt', 'srt', 'vtt', 'json']
                )
                
                # Check all formats were created
                output_path = Path(temp_output_dir)
                assert (output_path / "test_video_-_clipscribe_demo.txt").exists()
                assert (output_path / "test_video_-_clipscribe_demo.srt").exists()
                assert (output_path / "test_video_-_clipscribe_demo.vtt").exists()
                assert (output_path / "test_video_-_clipscribe_demo.json").exists()
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, temp_output_dir):
        """Test cost tracking throughout workflow."""
        # Setup mocks
        def mock_download(urls):
            audio_path = Path(temp_output_dir) / "test_video.m4a"
            create_test_audio_file(audio_path, duration_seconds=180.0)  # 3 minutes
            return None
        
        mock_ydl = Mock()
        mock_info = get_mock_yt_dlp_info()
        mock_info['duration'] = 180  # 3 minutes
        mock_ydl.extract_info.return_value = mock_info
        mock_ydl.download = mock_download
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_response = Mock()
                mock_response.text = "Transcribed text"
                mock_model.return_value.generate_content_async = AsyncMock(
                    return_value=mock_response
                )
                
                client = UniversalVideoClient()
                result = await client.transcribe_video(
                    TEST_VIDEO_URL,
                    output_dir=temp_output_dir
                )
                
                # Check cost calculation (3 minutes = $0.006)
                assert result.processing_cost == 0.006
                assert result.metadata.duration == 180
    
    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """Test progress reporting during workflow."""
        progress_updates = []
        
        def progress_callback(status: str, progress: float):
            progress_updates.append((status, progress))
        
        # Setup mocks
        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = get_mock_yt_dlp_info()
        mock_ydl.download.return_value = None
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_response = Mock()
                mock_response.text = "Transcribed"
                mock_model.return_value.generate_content_async = AsyncMock(
                    return_value=mock_response
                )
                
                client = UniversalVideoClient()
                await client.transcribe_video(
                    TEST_VIDEO_URL,
                    progress_callback=progress_callback
                )
                
                # Check progress updates were called
                assert len(progress_updates) > 0
                assert any("Extracting" in update[0] for update in progress_updates)
                assert any("Downloading" in update[0] for update in progress_updates)
                assert any("Transcribing" in update[0] for update in progress_updates)
    
    @pytest.mark.asyncio
    async def test_chimera_integration_format(self):
        """Test output format for Chimera integration."""
        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = get_mock_yt_dlp_info()
        mock_ydl.download.return_value = None
        
        with patch('yt_dlp.YoutubeDL', return_value=mock_ydl):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_response = Mock()
                mock_response.text = "Transcribed content"
                mock_model.return_value.generate_content_async = AsyncMock(
                    return_value=mock_response
                )
                
                client = UniversalVideoClient()
                result = await client.transcribe_video(TEST_VIDEO_URL)
                
                # Convert to Chimera format
                chimera_data = result.to_chimera_format()
                
                # Verify format
                assert "title" in chimera_data
                assert "href" in chimera_data
                assert "body" in chimera_data
                assert "metadata" in chimera_data
                assert chimera_data["metadata"]["source"] == "youtube"
                assert chimera_data["href"] == TEST_VIDEO_URL


class TestCLIIntegration:
    """Test CLI command integration."""
    
    @pytest.mark.asyncio
    async def test_cli_transcribe_command(self, temp_output_dir):
        """Test transcribe command through CLI."""
        from click.testing import CliRunner
        from clipscribe.commands.cli import cli
        
        runner = CliRunner()
        
        # Mock the video client
        mock_result = Mock(spec=VideoIntelligence)
        mock_result.transcript.full_text = "Test transcription"
        mock_result.metadata.title = "Test Video"
        mock_result.processing_cost = 0.002
        mock_result.processing_time = 2.5
        
        with patch('clipscribe.commands.cli.UniversalVideoClient') as mock_client:
            mock_instance = mock_client.return_value
            mock_instance.transcribe_video = AsyncMock(return_value=mock_result)
            
            result = runner.invoke(cli, [
                'transcribe',
                TEST_VIDEO_URL,
                '--output-dir', temp_output_dir
            ])
            
            assert result.exit_code == 0
            assert "Transcription complete!" in result.output
            assert "Test Video" in result.output
            assert "$0.002" in result.output  # :-) 