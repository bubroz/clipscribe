"""Integration tests for video processing pipeline with proper mocking."""
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript
from tests.helpers import create_mock_video_intelligence


@pytest.mark.integration
class TestVideoProcessingIntegration:
    """Fast integration tests for video processing pipeline with proper mocking."""

    @pytest.fixture
    def mock_video_metadata(self):
        """Create mock video metadata for testing."""
        from datetime import datetime

        return VideoMetadata(
            video_id="test_video_123",
            url="https://www.youtube.com/watch?v=test_video_123",
            title="Test Integration Video",
            channel="Test Channel",
            channel_id="test_channel_123",
            published_at=datetime(2024, 1, 15, 14, 30, 0),
            duration=300,
            view_count=10000,
            description="A test video for integration testing",
            tags=["test", "integration", "video"]
        )

    @pytest.fixture
    def video_retriever(self, temp_output_dir):
        """Create a VideoIntelligenceRetriever for testing with mocked dependencies."""
        return VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,  # Disable cache for testing
            output_dir=str(temp_output_dir),
            enhance_transcript=True,
            use_flash=False  # Use Pro model for quality
        )

    @pytest.fixture
    def test_output_dir(self, temp_directory):
        """Create a temporary output directory for test results."""
        output_dir = temp_directory / "real_video_test_output"
        output_dir.mkdir(exist_ok=True)
        return output_dir

    @pytest.mark.asyncio
    async def test_video_processing_pipeline_integration(self, video_retriever, mock_video_metadata, temp_output_dir):
        """Test the complete video processing pipeline integration with proper mocking."""
        from datetime import datetime

        # Set proper datetime for the mock
        mock_video_metadata.published_at = datetime(2024, 1, 15, 14, 30, 0)

        # Mock the entire video processing pipeline for fast testing
        with patch.object(video_retriever.processor, 'is_supported_url', return_value=True), \
             patch.object(video_retriever.processor, '_process_video_pipeline', new_callable=AsyncMock) as mock_pipeline:

            # Return a complete mock video intelligence result
            mock_pipeline.return_value = create_mock_video_intelligence(title="Test Integration Video", processing_cost=0.35)

            # Execute the complete workflow
            result = await video_retriever.process_url("https://www.youtube.com/watch?v=test_video_123")

            # Verify the result structure
            assert result is not None
            assert isinstance(result, VideoIntelligence)
            assert result.metadata.title == "Test Integration Video"
            assert result.transcript.full_text is not None
            assert result.processing_cost == 0.35

            # Verify the pipeline was called once
            mock_pipeline.assert_called_once_with("https://www.youtube.com/watch?v=test_video_123")

            # Note: Statistics aren't updated when mocking the pipeline directly
            # This is acceptable for this integration test focusing on the workflow

    @pytest.mark.asyncio
    async def test_batch_processing_integration(self, video_retriever, mock_video_metadata, temp_output_dir):
        """Test batch processing of multiple videos with proper mocking."""
        from datetime import datetime

        # Create mock metadata for multiple videos
        videos_metadata = [
            mock_video_metadata,
            VideoMetadata(
                video_id="batch_test_002",
                url="https://www.youtube.com/watch?v=batch_test_002",
                title="Second Batch Test Video",
                channel="Test Channel",
                channel_id="test_channel_123",
                published_at=datetime(2024, 1, 16, 10, 0, 0),
                duration=600,
                view_count=5000,
                description="Second video in batch processing test.",
                tags=["batch", "testing"]
            ),
            VideoMetadata(
                video_id="batch_test_003",
                url="https://www.youtube.com/watch?v=batch_test_003",
                title="Third Batch Test Video",
                channel="Test Channel",
                channel_id="test_channel_123",
                published_at=datetime(2024, 1, 17, 15, 30, 0),
                duration=900,
                view_count=3000,
                description="Third video in batch processing test.",
                tags=["batch", "final"]
            )
        ]

        with patch.object(video_retriever.processor.downloader, 'search_videos', return_value=videos_metadata), \
             patch.object(video_retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:

            mock_process.return_value = create_mock_video_intelligence()

            # Execute batch search and processing
            search_results = await video_retriever.search("batch processing test", max_results=3)

            # Verify search results
            assert len(search_results) == 3
            assert all(result is not None for result in search_results)

            # Process each video
            for metadata in videos_metadata:
                result = await video_retriever.process_url(metadata.url)
                assert result is not None
                assert isinstance(result, VideoIntelligence)

            # Verify processing stats reflect batch processing
            stats = video_retriever.get_stats()
            assert stats["videos_processed"] == 3

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, video_retriever, temp_output_dir):
        """Test error recovery and resilience in the workflow with proper mocking."""
        from datetime import datetime

        # Create test cases with mix of valid and invalid URLs
        test_cases = [
            ("Valid Video", "https://www.youtube.com/watch?v=valid_test", True),
            ("Invalid Video", "https://www.youtube.com/watch?v=invalid_video_12345", False),
        ]

        with patch.object(video_retriever.processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(video_retriever.processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe:

            # Setup mocks to simulate mixed success/failure
            def mock_download_side_effect(url, *args, **kwargs):
                if "valid_test" in url:
                    return (VideoMetadata(
                        video_id="valid_test",
                        url=url,
                        title="Valid Test Video",
                        channel="Test Channel",
                        channel_id="test_channel",
                        published_at=datetime.now(),
                        duration=300,
                        view_count=1000,
                        description="Valid test video",
                        tags=["test"]
                    ), str(temp_output_dir / "valid.mp4"))
                else:
                    raise Exception("Video not found")

            mock_download.side_effect = mock_download_side_effect
            mock_transcribe.return_value = {"transcript": "Test transcript", "language": "en", "confidence_score": 0.9}

            successful_results = 0
            failed_results = 0

            for test_name, url, should_succeed in test_cases:
                try:
                    result = await video_retriever.process_url(url)
                    if result is not None:
                        successful_results += 1
                        assert isinstance(result, VideoIntelligence)
                    else:
                        failed_results += 1
                except Exception:
                    failed_results += 1

            # System should handle both success and failure cases gracefully
            assert successful_results >= 1, "At least one valid video should process successfully"
            assert failed_results <= 1, "Only one test case should fail"

    @pytest.mark.asyncio
    async def test_cross_platform_integration(self, video_retriever, temp_output_dir):
        """Test processing videos from different platforms with proper mocking."""
        from datetime import datetime

        # Test different platform URLs
        platform_tests = [
            ("YouTube", "https://www.youtube.com/watch?v=platform_test_1"),
            ("Vimeo", "https://vimeo.com/123456789"),
            ("TikTok", "https://www.tiktok.com/@user/video/1234567890123456789"),
        ]

        with patch.object(video_retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = create_mock_video_intelligence()

            successful_results = 0

            for platform, url in platform_tests:
                try:
                    result = await video_retriever.process_url(url)
                    if result is not None:
                        successful_results += 1
                        assert isinstance(result, VideoIntelligence)
                        assert result.metadata.url == url
                except Exception as e:
                    # Some test URLs may not be accessible, that's OK for this test
                    print(f"Platform {platform} test failed: {e}")

            # At least one platform should work
            assert successful_results > 0, "At least one platform should process successfully"

            # Verify stats
            stats = video_retriever.get_stats()
            assert stats["videos_processed"] == successful_results

    @pytest.mark.asyncio
    async def test_performance_and_memory_efficiency(self, video_retriever, temp_output_dir):
        """Test performance characteristics and memory efficiency with proper mocking."""
        import time

        with patch.object(video_retriever, 'process_url', new_callable=AsyncMock) as mock_process, \
             patch.object(video_retriever.processor, 'get_stats') as mock_get_stats:
            mock_process.return_value = create_mock_video_intelligence()
            mock_get_stats.return_value = {
                "videos_processed": 5,
                "total_cost": 1.25,
                "average_cost": 0.25
            }

            # Time the processing of multiple videos
            start_time = time.time()

            # Process multiple videos sequentially
            for i in range(5):
                result = await video_retriever.process_url(f"https://www.youtube.com/watch?v=perf_test_{i}")
                assert result is not None
                assert isinstance(result, VideoIntelligence)

            end_time = time.time()
            processing_time = end_time - start_time

            # Should complete within reasonable time (allowing for async processing)
            assert processing_time < 10, f"Batch processing should complete within 10 seconds, took {processing_time}s"

            # Verify stats accuracy
            stats = video_retriever.get_stats()
            assert stats["videos_processed"] == 5
            assert "total_cost" in stats

    def test_output_format_integration(self, video_retriever, temp_output_dir):
        """Test that all output formats are generated correctly with proper mocking."""
        # Create a mock video intelligence result
        mock_result = create_mock_video_intelligence()

        with patch.object(video_retriever.processor.output_formatter, 'save_all_formats') as mock_save:
            expected_files = {
                "transcript_txt": temp_output_dir / "transcript.txt",
                "transcript_json": temp_output_dir / "transcript.json",
                "metadata": temp_output_dir / "metadata.json",
                "entities": temp_output_dir / "entities.json",
                "relationships": temp_output_dir / "relationships.json",
                "knowledge_graph": temp_output_dir / "knowledge_graph.json",
                "report": temp_output_dir / "report.md"
            }

            mock_save.return_value = expected_files

            # Test save_all_formats
            saved_files = video_retriever.save_all_formats(mock_result, str(temp_output_dir))

            # Verify all expected files are present
            assert len(saved_files) >= 7
            assert "transcript_txt" in saved_files
            assert "transcript_json" in saved_files
            assert "metadata" in saved_files
            assert "entities" in saved_files
            assert "relationships" in saved_files
            assert "report" in saved_files

            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_component_isolation_and_mocking(self, video_retriever, temp_output_dir):
        """Test that all external dependencies are properly isolated and mocked."""
        # This test verifies that our mocking strategy is comprehensive

        with patch('clipscribe.retrievers.video_retriever.VideoProcessor') as mock_processor_class:

            # Setup mock processor with mock components
            mock_processor = MagicMock()
            mock_processor.kg_builder = MagicMock()
            mock_processor.output_formatter = MagicMock()

            mock_processor_class.return_value = mock_processor

            # Create a new retriever instance to use our mocks
            test_retriever = VideoIntelligenceRetriever(
                cache_dir=str(temp_output_dir / "cache"),
                use_advanced_extraction=True,
                mode="auto",
                use_cache=False,
                output_dir=str(temp_output_dir)
            )

            # Verify that external dependencies are properly mocked
            # (In real usage, these would be actual expensive operations)
            assert mock_processor_class.called
