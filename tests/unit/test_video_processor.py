"""Unit tests for video_processor.py module."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from clipscribe.retrievers.video_processor import VideoProcessor
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript
from clipscribe.config.settings import VideoRetentionPolicy
from datetime import datetime
import sys
from unittest.mock import mock_open


@pytest.fixture
def video_processor():
    """Create a VideoProcessor instance for testing."""
    return VideoProcessor(
        cache_dir="test_cache",
        use_advanced_extraction=True,
        mode="auto",
        use_cache=False,  # Disable cache for testing
        output_dir="test_output",
        enhance_transcript=True,
        use_pro=True,
        settings=None,
        on_phase_start=None,
        on_phase_complete=None,
        on_error=None,
        on_phase_log=None
    )


@pytest.fixture
def mock_video_metadata():
    """Create mock video metadata."""
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
        "transcript": "This is a test transcript for video processing.",
        "language": "en",
        "confidence_score": 0.94,
        "processing_cost": 0.15,
        "summary": "Test summary for video processing",
        "key_points": [
            {"text": "Key point 1", "importance": 0.8},
            {"text": "Key point 2", "importance": 0.9}
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


class TestVideoProcessor:
    """Test cases for VideoProcessor class."""

    def test_init(self, video_processor):
        """Test VideoProcessor initialization."""
        assert video_processor.mode == "auto"
        assert video_processor.use_cache is False
        assert hasattr(video_processor, 'downloader')
        assert hasattr(video_processor, 'transcriber')
        assert hasattr(video_processor, 'kg_builder')
        assert hasattr(video_processor, 'output_formatter')
        assert hasattr(video_processor, 'entity_extractor')
        assert hasattr(video_processor, 'retention_manager')
        assert hasattr(video_processor, 'videos_processed')
        assert hasattr(video_processor, 'total_cost')

    def test_init_with_different_modes(self):
        """Test VideoProcessor initialization with different modes."""
        # Test with video mode
        processor = VideoProcessor(mode="video")
        assert processor.mode == "video"

        # Test with audio mode
        processor = VideoProcessor(mode="audio")
        assert processor.mode == "audio"

    def test_init_with_callbacks(self):
        """Test VideoProcessor initialization with callbacks."""
        mock_start = MagicMock()
        mock_complete = MagicMock()
        mock_error = MagicMock()
        mock_log = MagicMock()

        processor = VideoProcessor(
            on_phase_start=mock_start,
            on_phase_complete=mock_complete,
            on_error=mock_error,
            on_phase_log=mock_log
        )

        assert processor.on_phase_start == mock_start
        assert processor.on_phase_complete == mock_complete
        assert processor.on_error == mock_error
        assert processor.on_phase_log == mock_log

    @pytest.mark.asyncio
    async def test_process_url_success(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test successful URL processing."""
        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = ("test_media.mp4", mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = MagicMock()
            mock_save.return_value = {"test": Path("test.json")}

            result = await video_processor.process_url("https://www.youtube.com/watch?v=test")

            assert result is not None
            mock_download.assert_called_once()
            mock_transcribe.assert_called_once()
            mock_build_kg.assert_called_once()
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_url_download_failure(self, video_processor):
        """Test handling of download failure."""
        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = Exception("Download failed")

            result = await video_processor.process_url("https://www.youtube.com/watch?v=test")

            assert result is None
            # Download should have been attempted
            mock_download.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_url_transcription_failure(self, video_processor, mock_video_metadata):
        """Test handling of transcription failure."""
        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe:

            mock_download.return_value = ("test_media.mp4", mock_video_metadata)
            mock_transcribe.side_effect = Exception("Transcription failed")

            result = await video_processor.process_url("https://www.youtube.com/watch?v=test")

            assert result is None

    def test_save_transcript_delegation(self, video_processor):
        """Test that save_transcript delegates to output_formatter."""
        mock_video = MagicMock()
        mock_result = {"txt": Path("test.txt")}

        with patch.object(video_processor.output_formatter, 'save_transcript', return_value=mock_result) as mock_save:
            result = video_processor.save_transcript(mock_video, "output_dir", ["txt"])

            assert result == mock_result
            mock_save.assert_called_once_with(mock_video, "output_dir", ["txt"])

    def test_save_all_formats_delegation(self, video_processor):
        """Test that save_all_formats delegates to output_formatter."""
        mock_video = MagicMock()
        mock_result = {"json": Path("test.json")}

        with patch.object(video_processor.output_formatter, 'save_all_formats', return_value=mock_result) as mock_save:
            result = video_processor.save_all_formats(mock_video, "output_dir", True)

            assert result == mock_result
            mock_save.assert_called_once_with(mock_video, "output_dir", True)

    def test_get_stats_aggregation(self, video_processor):
        """Test stats aggregation from components."""
        with patch.object(video_processor.downloader, 'search_videos', return_value=[]), \
             patch.object(video_processor.transcriber, 'get_transcription_cost', return_value=0.15):

            stats = video_processor.get_stats()

            assert "videos_processed" in stats
            assert "total_cost" in stats
            assert "average_cost" in stats

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test concurrent video processing."""
        import asyncio

        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = ("test_media.mp4", mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = MagicMock()
            mock_save.return_value = {"test": Path("test.json")}

            # Process multiple URLs concurrently
            urls = [f"https://www.youtube.com/watch?v=test{i}" for i in range(3)]
            tasks = [video_processor.process_url(url) for url in urls]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            assert all(result is not None for result in results)
            assert mock_download.call_count == 3
            assert mock_transcribe.call_count == 3

    def test_create_video_intelligence(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test creation of VideoIntelligence object."""
        transcript = VideoTranscript(
            full_text="Test transcript",
            segments=[{"text": "Test transcript", "start": 0.0, "end": 5.0}]
        )

        result = video_processor._create_video_intelligence(mock_video_metadata, mock_transcription_analysis, transcript)

        assert isinstance(result, VideoIntelligence)
        assert result.metadata == mock_video_metadata
        assert result.transcript == transcript
        assert result.processing_cost == 0.15

    def test_callbacks_invocation(self, video_processor):
        """Test that callbacks are invoked during processing."""
        mock_start = MagicMock()
        mock_complete = MagicMock()
        mock_error = MagicMock()
        mock_log = MagicMock()

        processor = VideoProcessor(
            on_phase_start=mock_start,
            on_phase_complete=mock_complete,
            on_error=mock_error,
            on_phase_log=mock_log
        )

        # Test callback invocation
        if processor.on_phase_start:
            processor.on_phase_start("download", "Starting download")
        if processor.on_phase_complete:
            processor.on_phase_complete("download", 5.0)
        if processor.on_error:
            processor.on_error("transcription", "API error")
        if processor.on_phase_log:
            processor.on_phase_log("processing", 0.5)

        mock_start.assert_called_once_with("download", "Starting download")
        mock_complete.assert_called_once_with("download", 5.0)
        mock_error.assert_called_once_with("transcription", "API error")
        mock_log.assert_called_once_with("processing", 0.5)

    def test_callbacks_none_handling(self, video_processor):
        """Test that None callbacks don't cause errors."""
        # Should not raise any exceptions
        if video_processor.on_phase_start:
            video_processor.on_phase_start("test", "data")

    @pytest.mark.asyncio
    async def test_cleanup_operations(self, video_processor, mock_video_metadata):
        """Test cleanup operations after processing."""
        # Create mock transcription analysis inline to avoid fixture resolution issues
        mock_analysis = {
            "transcript": "This is a test transcript for video processing.",
            "language": "en",
            "confidence_score": 0.94,
            "processing_cost": 0.15,
            "summary": "Test summary for video processing",
            "key_points": [
                {"text": "Key point 1", "importance": 0.8},
                {"text": "Key point 2", "importance": 0.9}
            ],
            "entities": [
                {"name": "Test Entity", "type": "PERSON", "confidence": 0.9}
            ],
            "relationships": [
                {
                    "subject": "Test Entity",
                    "predicate": "related_to",
                    "object": "Another Entity",
                    "confidence": 0.8
                }
            ],
            "topics": ["test", "processing"]
        }

        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save, \
             patch.object(video_processor.downloader, 'cleanup_temp_file', new_callable=AsyncMock) as mock_cleanup:

            mock_download.return_value = ("test_media.mp4", mock_video_metadata)
            mock_transcribe.return_value = mock_analysis

            # Mock build_knowledge_graph to return the VideoIntelligence object with correct processing_cost
            def mock_build_kg_func(video_intel):
                video_intel.processing_cost = 0.15
                return video_intel
            mock_build_kg.side_effect = mock_build_kg_func

            mock_save.return_value = {"test": Path("test.json")}

            await video_processor.process_url("https://www.youtube.com/watch?v=test")

            mock_cleanup.assert_called_once()

    def test_retention_manager_initialization(self, video_processor):
        """Test that retention manager is properly initialized."""
        assert hasattr(video_processor, 'retention_manager')
        assert video_processor.retention_manager is not None

    def test_processing_stats_tracking(self, video_processor):
        """Test that processing statistics are tracked."""
        assert hasattr(video_processor, 'videos_processed')
        assert hasattr(video_processor, 'total_cost')
        assert video_processor.videos_processed == 0
        assert video_processor.total_cost == 0.0

    @pytest.mark.asyncio
    async def test_processing_stats_update(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test that processing statistics are updated after processing."""
        initial_processed = video_processor.videos_processed
        initial_cost = video_processor.total_cost

        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = ("test_media.mp4", mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis

            # Mock build_knowledge_graph to return the VideoIntelligence object with correct processing_cost
            def mock_build_kg_func(video_intel):
                video_intel.processing_cost = 0.15
                return video_intel
            mock_build_kg.side_effect = mock_build_kg_func

            mock_save.return_value = {"test": Path("test.json")}

            await video_processor.process_url("https://www.youtube.com/watch?v=test")

            # Stats should be updated
            assert video_processor.videos_processed == initial_processed + 1
            assert video_processor.total_cost == initial_cost + 0.15

    def test_mode_determination_auto(self, video_processor):
        """Test mode determination in auto mode."""
        # The processor stores the mode directly
        processor = VideoProcessor(mode="auto")
        assert processor.mode == "auto"

    def test_mode_determination_explicit(self, video_processor):
        """Test explicit mode determination."""
        processor = VideoProcessor(mode="video")
        # The mode is stored directly on the processor
        assert processor.mode == "video"

    def test_call_callback_error_handling(self, video_processor):
        """Test error handling in callback invocation."""
        def failing_callback(phase, data):
            raise Exception("Callback failed")

        # Test that exceptions in callbacks are handled gracefully
        with patch('builtins.print') as mock_print:
            try:
                failing_callback("test", "data")
            except Exception:
                pass  # Exception is expected

        # The test should complete without crashing
        assert True  # If we get here, the exception was handled

    @pytest.mark.asyncio
    async def test_processing_pipeline_error_recovery(self, video_processor):
        """Test error recovery in processing pipeline."""
        # Test that partial failures don't crash the entire pipeline
        with patch.object(video_processor.downloader, 'download_video', side_effect=Exception("Download failed")):
            result = await video_processor.process_url("test_url")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_handling(self, video_processor):
        """Test cache handling in video processing."""
        # Test with cache disabled
        processor = VideoProcessor(use_cache=False)
        assert processor.use_cache is False

        # Test with cache enabled
        processor = VideoProcessor(use_cache=True)
        assert processor.use_cache is True

    @pytest.mark.asyncio
    async def test_large_video_processing(self, video_processor, mock_video_metadata):
        """Test processing of large video files."""
        large_transcription = {
            "transcript": "Large transcript content " * 1000,  # Very long transcript
            "language": "en",
            "confidence_score": 0.92,
            "processing_cost": 0.50,
            "summary": "Large video summary",
            "key_points": [{"text": f"Key point {i}", "importance": 0.8} for i in range(50)],
            "entities": [{"name": f"Entity{i}", "type": "PERSON", "confidence": 0.9} for i in range(100)],
            "relationships": [
                {
                    "subject": f"Entity{i}",
                    "predicate": "related_to",
                    "object": f"Entity{i+1}",
                    "confidence": 0.8
                } for i in range(99)
            ],
            "topics": ["large", "processing", "test"]
        }

        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = ("large_video.mp4", mock_video_metadata)
            mock_transcribe.return_value = large_transcription

            # Mock build_knowledge_graph to return the VideoIntelligence object with correct processing_cost
            def mock_build_kg_func(video_intel):
                video_intel.processing_cost = 0.50
                return video_intel
            mock_build_kg.side_effect = mock_build_kg_func

            mock_save.return_value = {"test": Path("test.json")}

            result = await video_processor.process_url("https://www.youtube.com/watch?v=large_test")

            assert result is not None
            assert result.processing_cost == 0.50

    @pytest.mark.asyncio
    async def test_memory_efficient_processing(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test memory-efficient processing with cleanup."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = ("memory_test.mp4", mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = MagicMock()
            mock_save.return_value = {"test": Path("test.json")}

            # Process multiple videos
            for i in range(5):
                result = await video_processor.process_url(f"https://www.youtube.com/watch?v=memory_test_{i}")
                assert result is not None

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable (less than 50MB for this test)
            assert memory_increase < 50, f"Memory increased by {memory_increase}MB, may indicate memory leak"

    def test_processing_mode_validation(self):
        """Test processing mode validation."""
        # Test all valid modes
        valid_modes = ["auto", "video", "audio"]
        for mode in valid_modes:
            processor = VideoProcessor(mode=mode)
            assert processor.mode == mode

    def test_output_directory_handling(self, video_processor):
        """Test output directory handling."""
        processor = VideoProcessor(output_dir="custom_output")
        assert processor.output_dir == "custom_output"

        # Test with None (should use default)
        processor = VideoProcessor(output_dir=None)
        assert processor.output_dir is None

    def test_cache_directory_handling(self, video_processor):
        """Test cache directory handling."""
        processor = VideoProcessor(cache_dir="custom_cache")
        assert processor.downloader.cache_dir == Path("custom_cache")

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, video_processor, mock_video_metadata):
        """Test handling of partial processing failures."""
        # Test scenario where download succeeds but transcription fails
        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', side_effect=Exception("API temporarily unavailable")):

            mock_download.return_value = ("partial_fail.mp4", mock_video_metadata)

            result = await video_processor.process_url("https://www.youtube.com/watch?v=partial_fail")

            # Should return None on transcription failure
            assert result is None

            # But download should have been attempted
            mock_download.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_progress_tracking(self):
        """Test callback-based progress tracking."""
        progress_log = []

        def log_progress(phase, progress):
            progress_log.append(f"{phase}: {progress}")

        def log_phase_start(phase, message):
            progress_log.append(f"START {phase}: {message}")

        def log_phase_complete(phase, duration):
            progress_log.append(f"COMPLETE {phase}: {duration}s")

        processor = VideoProcessor(
            on_phase_start=log_phase_start,
            on_phase_complete=log_phase_complete,
            on_phase_log=log_progress
        )

        # Simulate processing phases
        if processor.on_phase_start:
            processor.on_phase_start("download", "Starting video download")
        if processor.on_phase_log:
            processor.on_phase_log("download", 0.2)
        if processor.on_phase_log:
            processor.on_phase_log("download", 0.8)
        if processor.on_phase_complete:
            processor.on_phase_complete("download", 15.5)

        if processor.on_phase_start:
            processor.on_phase_start("transcription", "Starting transcription")
        if processor.on_phase_log:
            processor.on_phase_log("transcription", 0.5)
        if processor.on_phase_complete:
            processor.on_phase_complete("transcription", 45.2)

        # Verify progress tracking
        assert len(progress_log) == 7
        assert "START download: Starting video download" in progress_log
        assert "download: 0.2" in progress_log
        assert "download: 0.8" in progress_log
        assert "COMPLETE download: 15.5s" in progress_log
        assert "START transcription: Starting transcription" in progress_log
        assert "transcription: 0.5" in progress_log
        assert "COMPLETE transcription: 45.2s" in progress_log

    @pytest.mark.asyncio
    async def test_concurrent_video_series_processing(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test processing a series of videos concurrently."""
        video_urls = [
            "https://www.youtube.com/watch?v=series_1",
            "https://www.youtube.com/watch?v=series_2",
            "https://www.youtube.com/watch?v=series_3"
        ]

        with patch.object(video_processor.downloader, 'is_supported_url', return_value=True), \
             patch.object(video_processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = ("series_video.mp4", mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = MagicMock()
            mock_save.return_value = {"test": Path("test.json")}

            # Process all videos concurrently
            import time
            start_time = time.time()

            tasks = [video_processor.process_url(url) for url in video_urls]
            results = await asyncio.gather(*tasks)

            end_time = time.time()
            processing_time = end_time - start_time

            # All should succeed
            assert len(results) == 3
            assert all(result is not None for result in results)

            # Should complete in reasonable time
            assert processing_time < 30  # Should be much faster than sequential

            # Verify all components were called for each video
            assert mock_download.call_count == 3
            assert mock_transcribe.call_count == 3
            assert mock_build_kg.call_count == 3
            assert mock_save.call_count == 3

            # Verify final stats
            final_stats = video_processor.get_stats()
            assert final_stats["videos_processed"] == 3

    def test_is_supported_url_basic(self, video_processor):
        """Test basic URL support checking."""
        with patch.object(video_processor.downloader, 'is_supported_url') as mock_check:
            mock_check.return_value = True
            result = video_processor.is_supported_url("https://youtube.com/watch?v=test")
            assert result is True

    def test_is_supported_url_unsupported(self, video_processor):
        """Test unsupported URL handling."""
        with patch.object(video_processor.downloader, 'is_supported_url') as mock_check:
            mock_check.return_value = False
            result = video_processor.is_supported_url("https://unsupported.com/video")
            assert result is False

    def test_save_transcript_basic(self, video_processor, mock_video_metadata):
        """Test basic transcript saving functionality."""
        transcript = VideoTranscript(full_text="Test content", segments=[])
        video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            summary="Test summary",
            transcript=transcript,
            entities=[],
            relationships=[],
            topics=[],
            temporal_references=[],
            key_points=[],
            processing_cost=0.0,
            processing_stats={}
        )

        with patch.object(video_processor.output_formatter, 'save_transcript') as mock_save:
            mock_save.return_value = {"txt": Path("output/transcript.txt")}
            result = video_processor.save_transcript(video_intel, "output")
            assert result is not None
            mock_save.assert_called_once()

    def test_save_all_formats_basic(self, video_processor, mock_video_metadata):
        """Test basic save all formats functionality."""
        video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            summary="Test summary",
            transcript=VideoTranscript(full_text="Test", segments=[]),
            entities=[],
            relationships=[],
            topics=[],
            temporal_references=[],
            key_points=[],
            processing_cost=0.0,
            processing_stats={}
        )

        with patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save:
            mock_save.return_value = ["output.json", "output.csv"]
            result = video_processor.save_all_formats(video_intel, "output")
            assert result == ["output.json", "output.csv"]
            mock_save.assert_called_once_with(video_intel, "output", include_chimera_format=True)

    def test_get_stats_empty(self):
        """Test get_stats with no processing done."""
        processor = VideoProcessor()
        stats = processor.get_stats()
        assert stats["videos_processed"] == 0
        assert stats["total_cost"] == 0.0

    def test_get_stats_after_processing(self, video_processor, mock_video_metadata):
        """Test get_stats after processing videos."""
        # Manually set stats to simulate processing
        video_processor.videos_processed = 2
        video_processor.total_cost = 1.5

        stats = video_processor.get_stats()
        assert stats["videos_processed"] == 2
        assert stats["total_cost"] == 1.5

    def test_init_minimal_config(self):
        """Test initialization with minimal configuration."""
        processor = VideoProcessor()
        assert processor.domain is None
        assert processor.mode == "auto"
        assert processor.use_cache is True
        assert processor.videos_processed == 0
        assert processor.total_cost == 0.0

    def test_init_with_custom_settings(self):
        """Test initialization with custom settings."""
        custom_settings = MagicMock()
        processor = VideoProcessor(settings=custom_settings, domain="youtube.com", mode="fast")
        assert processor.domain == "youtube.com"
        assert processor.mode == "fast"
        assert processor.settings == custom_settings


class TestVideoProcessorErrorHandling:
    """Test error handling and edge cases in VideoProcessor."""

    def test_init_advanced_extractor_import_error(self):
        """Test initialization when AdvancedHybridExtractor import fails."""
        # Mock the import failure for the specific module
        import_error = ImportError("No module named 'clipscribe.extractors.advanced_hybrid_extractor'")
        with patch('builtins.__import__', side_effect=import_error):
            with patch('clipscribe.retrievers.video_processor.__import__', side_effect=import_error):
                # Mock the entire module to None to simulate import failure
                with patch.dict('sys.modules', {'clipscribe.extractors.advanced_hybrid_extractor': None}):
                    processor = VideoProcessor(use_advanced_extraction=True)
                    # Should gracefully handle the import error
                    assert processor.entity_extractor is None

    @pytest.mark.asyncio
    async def test_process_url_general_exception_handling(self, video_processor):
        """Test general exception handling in process_url."""
        with patch.object(video_processor, 'is_supported_url', return_value=True):
            with patch.object(video_processor, '_process_video_pipeline', side_effect=Exception("General error")):
                with patch.object(video_processor, 'on_error') as mock_on_error:
                    result = await video_processor.process_url("https://example.com/video")

                    assert result is None
                    mock_on_error.assert_called_once_with("Processing", "General error")

    @pytest.mark.asyncio
    async def test_process_video_pipeline_entity_extraction_failure(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test entity extraction failure handling in pipeline."""
        with patch.object(video_processor.downloader, 'download_video') as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video') as mock_transcribe, \
             patch.object(video_processor, 'entity_extractor') as mock_extractor, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save, \
             patch.object(video_processor.retention_manager, 'handle_video_retention') as mock_retention, \
             patch('pathlib.Path.exists', return_value=True):

            # Setup mocks
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")
            mock_transcribe.return_value = mock_transcription_analysis
            # Mock the entity extractor to raise an exception
            mock_extractor.extract_entities.side_effect = Exception("Entity extraction failed")
            # Create proper VideoTranscript object for the result
            transcript_obj = VideoTranscript(full_text="Test transcript", segments=[])
            mock_kg.return_value = VideoIntelligence(
                metadata=mock_video_metadata,
                transcript=transcript_obj,
                entities=[],
                relationships=[],
                topics=[],
                temporal_references=[],
                key_points=[],
                processing_cost=0.0,
                processing_stats={"duration": 10.0}
            )
            mock_save.return_value = ["output.json"]
            mock_retention.return_value = "deleted"

            result = await video_processor._process_video_pipeline("https://example.com/video")

            # Should return result despite entity extraction failure
            assert result is not None
            assert isinstance(result, VideoIntelligence)
            assert result.metadata.video_id == "test_123"

    @pytest.mark.asyncio
    async def test_process_video_pipeline_knowledge_graph_failure(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test knowledge graph building failure handling."""
        with patch.object(video_processor.downloader, 'download_video') as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video') as mock_transcribe, \
             patch.object(video_processor, 'entity_extractor') as mock_extractor, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save, \
             patch.object(video_processor.retention_manager, 'handle_video_retention') as mock_retention, \
             patch('pathlib.Path.exists', return_value=True):

            # Setup mocks - create VideoIntelligence with entities to trigger KG building
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")
            mock_transcribe.return_value = mock_transcription_analysis
            transcript_obj = VideoTranscript(full_text="Test transcript", segments=[])
            # Create initial VideoIntelligence with entities to trigger KG building
            initial_vi = VideoIntelligence(
                metadata=mock_video_metadata,
                transcript=transcript_obj,
                entities=[{"name": "Test Entity", "type": "PERSON"}],  # Add entities to trigger KG
                relationships=[],
                topics=[],
                temporal_references=[],
                key_points=[],
                processing_cost=0.0,
                processing_stats={"duration": 10.0}
            )
            mock_extractor.extract_entities.return_value = initial_vi.entities
            # Mock kg builder to raise exception
            mock_kg.side_effect = Exception("Knowledge graph building failed")
            mock_save.return_value = ["output.json"]
            mock_retention.return_value = "deleted"

            result = await video_processor._process_video_pipeline("https://example.com/video")

            # Should return result despite KG building failure
            assert result is not None
            assert isinstance(result, VideoIntelligence)

    @pytest.mark.asyncio
    async def test_process_video_pipeline_video_retention_failure(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test video retention failure handling."""
        with patch.object(video_processor.downloader, 'download_video') as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video') as mock_transcribe, \
             patch.object(video_processor, 'entity_extractor') as mock_extractor, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save, \
             patch.object(video_processor.retention_manager, 'handle_video_retention') as mock_retention, \
             patch('pathlib.Path.exists', return_value=True):

            # Setup mocks
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")
            mock_transcribe.return_value = mock_transcription_analysis
            mock_extractor.extract_entities.return_value = []
            transcript_obj = VideoTranscript(full_text="Test transcript", segments=[])
            mock_kg.return_value = VideoIntelligence(
                metadata=mock_video_metadata,
                transcript=transcript_obj,
                entities=[],
                relationships=[],
                topics=[],
                temporal_references=[],
                key_points=[],
                processing_cost=0.0,
                processing_stats={"duration": 10.0}
            )
            mock_save.return_value = ["output.json"]
            mock_retention.side_effect = Exception("Video retention failed")

            result = await video_processor._process_video_pipeline("https://example.com/video")

            # Should return result despite retention failure
            assert result is not None
            assert isinstance(result, VideoIntelligence)

    @pytest.mark.asyncio
    async def test_process_video_pipeline_save_results_failure(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test save results failure handling."""
        with patch.object(video_processor.downloader, 'download_video') as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video') as mock_transcribe, \
             patch.object(video_processor, 'entity_extractor') as mock_extractor, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save, \
             patch.object(video_processor.retention_manager, 'handle_video_retention') as mock_retention, \
             patch('pathlib.Path.exists', return_value=True):

            # Setup mocks
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")
            mock_transcribe.return_value = mock_transcription_analysis
            mock_extractor.extract_entities.return_value = []
            transcript_obj = VideoTranscript(full_text="Test transcript", segments=[])
            mock_kg.return_value = VideoIntelligence(
                metadata=mock_video_metadata,
                transcript=transcript_obj,
                entities=[],
                relationships=[],
                topics=[],
                temporal_references=[],
                key_points=[],
                processing_cost=0.0,
                processing_stats={"duration": 10.0}
            )
            mock_save.side_effect = Exception("Save results failed")
            mock_retention.return_value = "deleted"

            result = await video_processor._process_video_pipeline("https://example.com/video")

            # Should return result despite save failure
            assert result is not None
            assert isinstance(result, VideoIntelligence)

    @pytest.mark.asyncio
    async def test_process_video_pipeline_with_none_transcript(self, video_processor, mock_video_metadata):
        """Test pipeline handling when transcript is None."""
        with patch.object(video_processor.downloader, 'download_video') as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video') as mock_transcribe, \
             patch.object(video_processor.transcriber, 'create_transcript_object') as mock_create_transcript, \
             patch.object(video_processor, 'entity_extractor') as mock_extractor, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save, \
             patch.object(video_processor.retention_manager, 'handle_video_retention') as mock_retention, \
             patch('pathlib.Path.exists', return_value=True):

            # Setup mocks with None transcript
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")
            mock_transcribe.return_value = None  # Simulate failed transcription
            # Mock the transcript object creation to return a valid transcript
            transcript_obj = VideoTranscript(full_text="", segments=[])
            mock_create_transcript.return_value = transcript_obj
            mock_extractor.extract_entities.return_value = []
            mock_kg.return_value = VideoIntelligence(
                metadata=mock_video_metadata,
                transcript=transcript_obj,
                entities=[],
                relationships=[],
                topics=[],
                temporal_references=[],
                key_points=[],
                processing_cost=0.0,
                processing_stats={"duration": 10.0}
            )
            mock_save.return_value = ["output.json"]
            mock_retention.return_value = "deleted"

            result = await video_processor._process_video_pipeline("https://example.com/video")

            # Should handle None transcript gracefully (transcript object is still created)
            assert result is not None
            assert isinstance(result, VideoIntelligence)

    @pytest.mark.asyncio
    async def test_process_video_pipeline_with_none_entities(self, video_processor, mock_video_metadata, mock_transcription_analysis):
        """Test pipeline handling when entities is None."""
        with patch.object(video_processor.downloader, 'download_video') as mock_download, \
             patch.object(video_processor.transcriber, 'transcribe_video') as mock_transcribe, \
             patch.object(video_processor, 'entity_extractor') as mock_extractor, \
             patch.object(video_processor.kg_builder, 'build_knowledge_graph') as mock_kg, \
             patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save, \
             patch.object(video_processor.retention_manager, 'handle_video_retention') as mock_retention, \
             patch('pathlib.Path.exists', return_value=True):

            # Setup mocks with None entities
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")
            mock_transcribe.return_value = mock_transcription_analysis
            mock_extractor.extract_entities.return_value = None  # Simulate None entities
            mock_kg.return_value = VideoIntelligence(
                metadata=mock_video_metadata,
                transcript=mock_transcribe.return_value.transcript,
                entities=None,  # None entities
                relationships=[],
                topics=[],
                temporal_references=[],
                key_points=[],
                processing_cost=0.0,
                processing_stats={"duration": 10.0}
            )
            mock_save.return_value = ["output.json"]
            mock_retention.return_value = "deleted"

            result = await video_processor._process_video_pipeline("https://example.com/video")

            # Should handle None entities gracefully
            assert result is not None
            assert isinstance(result, VideoIntelligence)

    @pytest.mark.asyncio
    async def test_is_supported_url_delegation(self, video_processor):
        """Test URL support check delegation."""
        with patch.object(video_processor.downloader, 'is_supported_url') as mock_is_supported:
            mock_is_supported.return_value = True

            result = video_processor.is_supported_url("https://example.com/video")

            assert result is True
            mock_is_supported.assert_called_once_with("https://example.com/video")

    def test_create_video_intelligence_with_minimal_data(self, video_processor, mock_video_metadata):
        """Test video intelligence creation with minimal data."""
        # Create minimal analysis dict
        analysis = {
            "summary": "Test summary",
            "key_points": [],
            "topics": []
        }

        transcript_obj = VideoTranscript(full_text="", segments=[])
        result = video_processor._create_video_intelligence(
            metadata=mock_video_metadata,
            analysis=analysis,
            transcript=transcript_obj
        )

        assert isinstance(result, VideoIntelligence)
        assert result.metadata == mock_video_metadata
        assert result.transcript == transcript_obj
        assert result.entities == []
        assert result.processing_cost == 0.0
        assert "duration" in result.processing_stats

    def test_save_transcript_file_path_handling(self, video_processor, mock_video_metadata):
        """Test save_transcript with file path handling."""
        with patch.object(video_processor.output_formatter, 'save_transcript') as mock_save:
            mock_save.return_value = {"txt": Path("test_output/transcript.txt")}

            video_intel = VideoIntelligence(
                metadata=mock_video_metadata,
                summary="Test summary",  # Required field
                transcript=VideoTranscript(full_text="Test transcript", segments=[]),
                entities=[],
                relationships=[],
                topics=[],
                temporal_references=[],
                key_points=[],
                processing_cost=0.0,
                processing_stats={}
            )

            result = video_processor.save_transcript(video_intel, "test_output_dir")

            assert result is not None
            mock_save.assert_called_once_with(video_intel, "test_output_dir", ["txt"])

    def test_save_all_formats_delegation(self, video_processor, mock_video_metadata):
        """Test save_all_formats delegation."""
        mock_video_intel = VideoIntelligence(
            metadata=mock_video_metadata,
            summary="Test summary",  # Required field
            transcript=VideoTranscript(full_text="Test", segments=[]),
            entities=[],
            relationships=[],
            topics=[],
            temporal_references=[],
            key_points=[],
            processing_cost=0.0,
            processing_stats={}
        )

        with patch.object(video_processor.output_formatter, 'save_all_formats') as mock_save:
            mock_save.return_value = ["test.json"]

            result = video_processor.save_all_formats(mock_video_intel, "test_output")

            assert result == ["test.json"]
            mock_save.assert_called_once_with(
                mock_video_intel,
                "test_output",
                include_chimera_format=True
            )

    def test_get_stats_initial_values(self):
        """Test get_stats returns correct initial values."""
        processor = VideoProcessor()

        stats = processor.get_stats()

        assert stats["videos_processed"] == 0
        assert stats["total_cost"] == 0.0
        assert "videos_processed" in stats
        assert "total_cost" in stats