"""Integration tests for refactored modular components."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from clipscribe.retrievers.video_processor import VideoProcessor
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript
from tests.helpers import create_mock_video_intelligence
from datetime import datetime


@pytest.mark.integration
class TestRefactoredModulesIntegration:
    """Integration tests for the refactored modular components."""

    @pytest.fixture
    def mock_video_metadata(self):
        """Create comprehensive mock video metadata."""
        return VideoMetadata(
            video_id="integration_test_123",
            url="https://www.youtube.com/watch?v=integration123",
            title="Integration Test Video",
            channel="Integration Test Channel",
            channel_id="integration_channel",
            published_at=datetime.now(),
            duration=600,  # 10 minutes
            view_count=50000,
            description="A comprehensive integration test video",
            tags=["integration", "test", "clipscribe"]
        )

    @pytest.fixture
    def mock_transcription_analysis(self):
        """Create comprehensive mock transcription analysis."""
        return {
            "transcript": "This is a comprehensive integration test transcript with multiple sentences and various topics.",
            "language": "en",
            "confidence_score": 0.92,
            "processing_cost": 0.25,
            "summary": "Integration test summary demonstrating the full pipeline functionality.",
            "key_points": [
                {"text": "First key point from integration test", "importance": 0.9},
                {"text": "Second key point with technical details", "importance": 0.8},
                {"text": "Third key point about results", "importance": 0.7}
            ],
            "entities": [
                {"name": "ClipScribe", "type": "SOFTWARE", "confidence": 0.95},
                {"name": "Google", "type": "ORGANIZATION", "confidence": 0.88},
                {"name": "John Doe", "type": "PERSON", "confidence": 0.91}
            ],
            "relationships": [
                {
                    "subject": "ClipScribe",
                    "predicate": "uses",
                    "object": "Google Gemini",
                    "confidence": 0.85,
                    "extraction_source": "REBEL"
                },
                {
                    "subject": "John Doe",
                    "predicate": "works_at",
                    "object": "Google",
                    "confidence": 0.82,
                    "extraction_source": "REBEL"
                }
            ],
            "topics": ["technology", "AI", "video processing", "integration testing"]
        }

    @pytest.mark.asyncio
    async def test_full_video_processing_pipeline(self, mock_video_metadata, mock_transcription_analysis, temp_output_dir):
        """Test the complete video processing pipeline end-to-end."""
        processor = VideoProcessor(
            cache_dir=temp_output_dir / "cache",
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,  # Disable cache for testing
            output_dir=str(temp_output_dir),
            enhance_transcript=True
        )

        with patch.object(processor, 'is_supported_url', return_value=True), \
             patch.object(processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = (str(temp_output_dir / "test_video.mp4"), mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = create_mock_video_intelligence(processing_cost=0.25)
            mock_save.return_value = {
                "transcript_txt": temp_output_dir / "transcript.txt",
                "transcript_json": temp_output_dir / "transcript.json",
                "metadata": temp_output_dir / "metadata.json",
                "entities": temp_output_dir / "entities.json",
                "relationships": temp_output_dir / "relationships.json"
            }

            result = await processor.process_url("https://www.youtube.com/watch?v=integration123")

            # Verify the pipeline executed correctly
            assert result is not None
            mock_download.assert_called_once()
            mock_transcribe.assert_called_once()
            mock_build_kg.assert_called_once()
            mock_save.assert_called_once()

            # Verify processing stats were updated
            stats = processor.get_stats()
            assert stats["videos_processed"] == 1
            assert stats["total_cost"] == 0.25

    @pytest.mark.asyncio
    async def test_video_retriever_facade_integration(self, mock_video_metadata, mock_transcription_analysis, temp_output_dir):
        """Test VideoIntelligenceRetriever as facade to the modular components."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir),
            enhance_transcript=True,
            use_flash=False  # This internally sets use_pro=True
        )

        with patch.object(retriever.processor, 'is_supported_url', return_value=True), \
             patch.object(retriever.processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(retriever.processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(retriever.processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(retriever.processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = (str(temp_output_dir / "test_video.mp4"), mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = create_mock_video_intelligence()
            mock_save.return_value = {"test": Path("test.json")}

            # Test process_url through facade
            result = await retriever.process_url("https://www.youtube.com/watch?v=facade_test")

            assert result is not None
            mock_download.assert_called_once()
            mock_transcribe.assert_called_once()

            # Test save_transcript through facade
            with patch.object(retriever.processor, 'save_transcript') as mock_save_transcript:
                mock_save_transcript.return_value = {"txt": Path("transcript.txt")}
                saved_files = retriever.save_transcript(result, str(temp_output_dir), ["txt"])
                mock_save_transcript.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_processing_stress_test(self, mock_video_metadata, mock_transcription_analysis, temp_output_dir):
        """Stress test with concurrent video processing."""
        processor = VideoProcessor(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=False,  # Disable for faster testing
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        async def mock_process_single(url):
            """Mock processing for a single video."""
            with patch.object(processor, 'is_supported_url', return_value=True), \
                 patch.object(processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
                 patch.object(processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
                 patch.object(processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
                 patch.object(processor.output_formatter, 'save_all_formats') as mock_save:

                mock_download.return_value = (str(temp_output_dir / f"test_video_{url.split('=')[-1]}.mp4"), mock_video_metadata)
                mock_transcribe.return_value = mock_transcription_analysis
                mock_build_kg.return_value = create_mock_video_intelligence()
                mock_save.return_value = {"test": Path("test.json")}

                return await processor.process_url(url)

        # Process 5 videos concurrently
        urls = [f"https://www.youtube.com/watch?v=concurrent{i}" for i in range(5)]
        tasks = [mock_process_single(url) for url in urls]

        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # All should complete successfully
        assert len(results) == 5
        assert all(result is not None for result in results)

        # Should complete within reasonable time (allowing for async processing)
        duration = end_time - start_time
        assert duration < 30  # Should complete within 30 seconds

        # Stats should reflect all processing
        final_stats = processor.get_stats()
        assert final_stats["videos_processed"] == 5

    def test_error_recovery_and_resilience(self, temp_output_dir):
        """Test error recovery and system resilience."""
        processor = VideoProcessor(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        # Test with download failure
        with patch.object(processor, 'is_supported_url', return_value=True), \
             patch.object(processor.downloader, 'download_video', side_effect=Exception("Network error")):
            result = asyncio.run(processor.process_url("https://www.youtube.com/watch?v=error_test"))
            assert result is None

        # Test with transcription failure after successful download
        error_metadata = VideoMetadata(
            video_id="error_test",
            url="https://www.youtube.com/watch?v=error_test",
            title="Error Test",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=datetime.now(),
            duration=300,
            view_count=1000,
            description="Error test video",
            tags=["test"]
        )

        with patch.object(processor, 'is_supported_url', return_value=True), \
             patch.object(processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(processor.transcriber, 'transcribe_video', side_effect=Exception("API error")):

            mock_download.return_value = (str(temp_output_dir / "error_video.mp4"), error_metadata)

            result = asyncio.run(processor.process_url("https://www.youtube.com/watch?v=error_test"))
            assert result is None

        # System should remain functional for subsequent requests
        recovery_metadata = VideoMetadata(
            video_id="recovery_test",
            url="https://www.youtube.com/watch?v=recovery_test",
            title="Recovery Test",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=datetime.now(),
            duration=300,
            view_count=1000,
            description="Recovery test video",
            tags=["test"]
        )

        with patch.object(processor, 'is_supported_url', return_value=True), \
             patch.object(processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = (str(temp_output_dir / "recovery_video.mp4"), recovery_metadata)
            mock_transcribe.return_value = {"transcript": "Recovery test", "language": "en"}
            mock_build_kg.return_value = create_mock_video_intelligence()
            mock_save.return_value = {"test": Path("test.json")}

            result = asyncio.run(processor.process_url("https://www.youtube.com/watch?v=recovery_test"))
            assert result is not None

    @pytest.mark.asyncio
    async def test_search_and_process_integration(self, mock_video_metadata, mock_transcription_analysis, temp_output_dir):
        """Test the search and process integration."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        # Mock search results
        search_results = [mock_video_metadata]

        with patch.object(retriever.processor.downloader, 'search_videos', return_value=search_results), \
             patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:

            mock_process.return_value = create_mock_video_intelligence()

            # Test search and processing
            results = await retriever.search("integration test query", max_results=1)

            assert len(results) == 1
            retriever.processor.downloader.search_videos.assert_called_once_with("integration test query", 1, "youtube")
            mock_process.assert_called_once_with(mock_video_metadata.url)

    def test_callback_integration(self, temp_output_dir):
        """Test callback system integration."""
        callback_calls = []

        def mock_phase_start(phase, message):
            callback_calls.append(f"START: {phase} - {message}")

        def mock_phase_complete(phase, duration):
            callback_calls.append(f"COMPLETE: {phase} - {duration}s")

        def mock_error(phase, error):
            callback_calls.append(f"ERROR: {phase} - {error}")

        def mock_phase_log(phase, progress):
            callback_calls.append(f"LOG: {phase} - {progress}")

        processor = VideoProcessor(
            cache_dir=str(temp_output_dir / "cache"),
            on_phase_start=mock_phase_start,
            on_phase_complete=mock_phase_complete,
            on_error=mock_error,
            on_phase_log=mock_phase_log
        )

        # Test callback invocation
        processor._call_callback(processor.on_phase_start, "download", "Starting download")
        processor._call_callback(processor.on_phase_complete, "download", 5.0)
        processor._call_callback(processor.on_error, "transcription", "API error")
        processor._call_callback(processor.on_phase_log, "processing", 0.5)

        assert len(callback_calls) == 4
        assert "START: download - Starting download" in callback_calls
        assert "COMPLETE: download - 5.0s" in callback_calls
        assert "ERROR: transcription - API error" in callback_calls
        assert "LOG: processing - 0.5" in callback_calls

    @pytest.mark.asyncio
    async def test_retention_policy_integration(self, mock_video_metadata, mock_transcription_analysis, temp_output_dir):
        """Test retention policy integration with video processing."""
        from clipscribe.config.settings import VideoRetentionPolicy

        processor = VideoProcessor(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=False,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        # Create a temporary video file
        temp_video = temp_output_dir / "temp_video.mp4"
        temp_video.write_text("test video content")

        with patch.object(processor, 'is_supported_url', return_value=True), \
             patch.object(processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = (str(temp_video), mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = create_mock_video_intelligence()
            mock_save.return_value = {"test": Path("test.json")}

            # Process with NONE retention policy
            processor.settings.video_retention_policy = VideoRetentionPolicy.DELETE

            result = await processor.process_url("https://www.youtube.com/watch?v=retention_test")

            # Video file should be cleaned up
            assert not temp_video.exists()

    @pytest.mark.asyncio
    async def test_processing_stats_accuracy(self, mock_video_metadata, mock_transcription_analysis, temp_output_dir):
        """Test that processing statistics are accurately tracked."""
        processor = VideoProcessor(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        initial_stats = processor.get_stats()
        assert initial_stats["videos_processed"] == 0
        assert initial_stats["total_cost"] == 0.0

        with patch.object(processor, 'is_supported_url', return_value=True), \
             patch.object(processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = (str(temp_output_dir / "stats_video.mp4"), mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = create_mock_video_intelligence(processing_cost=0.25)
            mock_save.return_value = {"test": Path("test.json")}

            # Process multiple videos
            for i in range(3):
                await processor.process_url(f"https://www.youtube.com/watch?v=stats_test_{i}")

            final_stats = processor.get_stats()
            assert final_stats["videos_processed"] == 3
            assert final_stats["total_cost"] == 0.75  # 3 * 0.25
            assert final_stats["average_cost"] == 0.25  # 0.75 / 3

    def test_module_initialization_integration(self, temp_output_dir):
        """Test that all modules are properly initialized and connected."""
        processor = VideoProcessor(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=True,
            output_dir=str(temp_output_dir)
        )

        # Verify all components are initialized
        assert processor.downloader is not None
        assert processor.transcriber is not None
        assert processor.kg_builder is not None
        assert processor.output_formatter is not None
        assert processor.entity_extractor is not None
        assert processor.retention_manager is not None

        # Verify component relationships
        assert processor.downloader.cache_dir == Path(temp_output_dir / "cache")
        assert processor.transcriber.use_pro is True
        assert processor.mode == "auto"
        assert processor.use_advanced_extraction is True

        # Verify settings integration
        assert processor.settings is not None

    @pytest.mark.asyncio
    async def test_api_compatibility_verification(self, mock_video_metadata, mock_transcription_analysis, temp_output_dir):
        """Verify API compatibility between old and new interfaces."""
        # Test the new modular processor
        processor = VideoProcessor(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        with patch.object(processor, 'is_supported_url', return_value=True), \
             patch.object(processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = (str(temp_output_dir / "api_test.mp4"), mock_video_metadata)
            mock_transcribe.return_value = mock_transcription_analysis
            mock_build_kg.return_value = create_mock_video_intelligence()
            mock_save.return_value = {"test": Path("test.json")}

            # Test all public methods exist and work
            result = await processor.process_url("https://www.youtube.com/watch?v=api_test")
            assert result is not None

            saved_files = processor.save_transcript(result, str(temp_output_dir), ["txt"])
            assert isinstance(saved_files, dict)

            all_formats = processor.save_all_formats(result, str(temp_output_dir))
            assert isinstance(all_formats, dict)

            stats = processor.get_stats()
            assert isinstance(stats, dict)
            assert "videos_processed" in stats
            assert "total_cost" in stats

        # Test the facade retriever
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = create_mock_video_intelligence()

            # Test facade methods delegate correctly
            result = await retriever.process_url("https://www.youtube.com/watch?v=facade_api_test")
            assert result is not None

            search_results = await retriever.search("api compatibility test", max_results=1)
            assert isinstance(search_results, list)

            saved = retriever.save_transcript(result, str(temp_output_dir), ["txt"])
            assert isinstance(saved, dict)

            all_saved = retriever.save_all_formats(result, str(temp_output_dir))
            assert isinstance(all_saved, dict)

            stats = retriever.get_stats()
            assert isinstance(stats, dict)
