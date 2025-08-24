"""End-to-end workflow tests for the refactored ClipScribe system."""
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript
from tests.helpers import create_mock_video_intelligence
from datetime import datetime


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end tests for complete ClipScribe workflows."""

    @pytest.fixture
    def comprehensive_video_metadata(self):
        """Create comprehensive video metadata for testing."""
        return VideoMetadata(
            video_id="e2e_test_001",
            url="https://www.youtube.com/watch?v=comprehensive_test",
            title="Comprehensive End-to-End Test Video",
            channel="ClipScribe Testing Channel",
            channel_id="clipscribe_testing",
            published_at=datetime(2024, 1, 15, 14, 30, 0),
            duration=1800,  # 30 minutes
            view_count=150000,
            description="A comprehensive test video covering all ClipScribe features and functionality.",
            tags=["clipscribe", "testing", "AI", "video processing", "end-to-end"]
        )

    @pytest.fixture
    def comprehensive_transcription_analysis(self):
        """Create comprehensive transcription analysis data."""
        return {
            "transcript": """
            Welcome to this comprehensive end-to-end test of ClipScribe's video intelligence capabilities.
            Today we're testing the complete pipeline from video download to knowledge graph generation.
            ClipScribe uses Google's Gemini 2.5 Flash model for high-accuracy transcription at 92% lower cost than traditional services.
            The system supports 1800+ video platforms through yt-dlp integration and provides advanced entity extraction using hybrid techniques.
            Key features include temporal intelligence, relationship extraction, and comprehensive output formats.
            We're particularly interested in how the system handles complex multi-speaker conversations and technical content.
            The modular architecture allows for scalable processing and easy maintenance.
            """.strip(),
            "language": "en",
            "confidence_score": 0.94,
            "processing_cost": 0.35,
            "summary": "Comprehensive demonstration of ClipScribe's end-to-end video intelligence pipeline including transcription, entity extraction, relationship mapping, and knowledge graph generation.",
            "key_points": [
                {
                    "text": "ClipScribe uses Google's Gemini 2.5 Flash for 92% cost reduction",
                    "importance": 0.95,
                    "timestamp": "00:02:15"
                },
                {
                    "text": "Supports 1800+ video platforms through yt-dlp integration",
                    "importance": 0.9,
                    "timestamp": "00:03:45"
                },
                {
                    "text": "Hybrid entity extraction with temporal intelligence",
                    "importance": 0.88,
                    "timestamp": "00:05:20"
                },
                {
                    "text": "Modular architecture enables scalable processing",
                    "importance": 0.85,
                    "timestamp": "00:07:10"
                },
                {
                    "text": "Comprehensive output formats for different use cases",
                    "importance": 0.82,
                    "timestamp": "00:08:30"
                }
            ],
            "entities": [
                {
                    "name": "ClipScribe",
                    "type": "SOFTWARE",
                    "confidence": 0.96,
                    "mention_count": 5,
                    "context_windows": [
                        {"text": "ClipScribe uses Google's Gemini", "start": 45, "end": 75}
                    ]
                },
                {
                    "name": "Google",
                    "type": "ORGANIZATION",
                    "confidence": 0.92,
                    "mention_count": 2,
                    "context_windows": [
                        {"text": "Google's Gemini 2.5 Flash model", "start": 120, "end": 150}
                    ]
                },
                {
                    "name": "Gemini 2.5 Flash",
                    "type": "MODEL",
                    "confidence": 0.89,
                    "mention_count": 2,
                    "context_windows": [
                        {"text": "Gemini 2.5 Flash model for high-accuracy", "start": 140, "end": 180}
                    ]
                },
                {
                    "name": "yt-dlp",
                    "type": "SOFTWARE",
                    "confidence": 0.87,
                    "mention_count": 1,
                    "context_windows": [
                        {"text": "through yt-dlp integration", "start": 200, "end": 230}
                    ]
                }
            ],
            "relationships": [
                {
                    "subject": "ClipScribe",
                    "predicate": "uses",
                    "object": "Gemini 2.5 Flash",
                    "confidence": 0.91,
                    "extraction_source": "REBEL",
                    "evidence_chain": [
                        "ClipScribe uses Google's Gemini 2.5 Flash model",
                        "Gemini 2.5 Flash for high-accuracy transcription"
                    ]
                },
                {
                    "subject": "ClipScribe",
                    "predicate": "integrates_with",
                    "object": "yt-dlp",
                    "confidence": 0.85,
                    "extraction_source": "REBEL",
                    "evidence_chain": [
                        "Supports 1800+ video platforms through yt-dlp integration"
                    ]
                },
                {
                    "subject": "ClipScribe",
                    "predicate": "provides",
                    "object": "temporal intelligence",
                    "confidence": 0.88,
                    "extraction_source": "REBEL",
                    "evidence_chain": [
                        "Hybrid entity extraction with temporal intelligence"
                    ]
                }
            ],
            "topics": [
                "artificial intelligence",
                "video processing",
                "machine learning",
                "entity extraction",
                "relationship mapping",
                "knowledge graphs",
                "software architecture"
            ]
        }

    @pytest.mark.asyncio
    async def test_complete_single_video_workflow(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test complete workflow for processing a single video end-to-end."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir),
            enhance_transcript=True,
            use_pro=True
        )

        # Mock all the external dependencies
        with patch.object(retriever.processor.downloader, 'download_video', new_callable=AsyncMock) as mock_download, \
             patch.object(retriever.processor.transcriber, 'transcribe_video', new_callable=AsyncMock) as mock_transcribe, \
             patch.object(retriever.processor.kg_builder, 'build_knowledge_graph') as mock_build_kg, \
             patch.object(retriever.processor.output_formatter, 'save_all_formats') as mock_save:

            mock_download.return_value = (comprehensive_video_metadata, str(temp_output_dir / "e2e_video.mp4"))
            mock_transcribe.return_value = comprehensive_transcription_analysis
            mock_build_kg.return_value = create_mock_video_intelligence()
            mock_save.return_value = {
                "transcript_txt": temp_output_dir / "transcript.txt",
                "transcript_json": temp_output_dir / "transcript.json",
                "metadata": temp_output_dir / "metadata.json",
                "entities": temp_output_dir / "entities.json",
                "relationships": temp_output_dir / "relationships.json",
                "knowledge_graph": temp_output_dir / "knowledge_graph.json",
                "report": temp_output_dir / "report.md"
            }

            # Execute the complete workflow
            video_intelligence = await retriever.process_url("https://www.youtube.com/watch?v=comprehensive_test")

            # Verify the result
            assert video_intelligence is not None
            assert video_intelligence.metadata.title == "Comprehensive End-to-End Test Video"
            assert video_intelligence.metadata.duration == 1800
            assert video_intelligence.processing_cost == 0.35

            # Verify all components were called
            mock_download.assert_called_once()
            mock_transcribe.assert_called_once()
            mock_build_kg.assert_called_once()
            mock_save.assert_called_once()

            # Verify processing statistics
            stats = retriever.get_stats()
            assert stats["videos_processed"] == 1
            assert stats["total_cost"] == 0.35

    @pytest.mark.asyncio
    async def test_batch_processing_workflow(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test batch processing of multiple videos."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        # Create mock search results
        search_results = [
            comprehensive_video_metadata,
            VideoMetadata(
                video_id="e2e_test_002",
                url="https://www.youtube.com/watch?v=batch_test_2",
                title="Second Batch Test Video",
                channel="ClipScribe Testing Channel",
                channel_id="clipscribe_testing",
                published_at=datetime(2024, 1, 16, 10, 0, 0),
                duration=1200,
                view_count=75000,
                description="Second video in batch processing test.",
                tags=["batch", "testing"]
            ),
            VideoMetadata(
                video_id="e2e_test_003",
                url="https://www.youtube.com/watch?v=batch_test_3",
                title="Third Batch Test Video",
                channel="ClipScribe Testing Channel",
                channel_id="clipscribe_testing",
                published_at=datetime(2024, 1, 17, 15, 30, 0),
                duration=900,
                view_count=45000,
                description="Third video in batch processing test.",
                tags=["batch", "final"]
            )
        ]

        with patch.object(retriever.processor.downloader, 'search_videos', return_value=search_results), \
             patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:

            mock_process.return_value = create_mock_video_intelligence()

            # Execute batch search and processing
            results = await retriever.search("end-to-end testing", max_results=3)

            # Verify results
            assert len(results) == 3
            assert all(result is not None for result in results)

            # Verify search was called correctly
            retriever.processor.downloader.search_videos.assert_called_once_with("end-to-end testing", 3, "youtube")

            # Verify each video was processed
            assert mock_process.call_count == 3

            # Verify processing stats reflect batch processing
            stats = retriever.get_stats()
            assert stats["videos_processed"] == 3

    @pytest.mark.asyncio
    async def test_different_output_formats_workflow(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test different output format combinations."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = create_mock_video_intelligence()

            # Process the video
            video_intelligence = await retriever.process_url("https://www.youtube.com/watch?v=format_test")

            # Test different output format combinations
            test_cases = [
                (["txt"], "Text only"),
                (["json"], "JSON only"),
                (["txt", "json"], "Text and JSON"),
                (["txt", "json", "md"], "All text formats")
            ]

            for formats, description in test_cases:
                with patch.object(retriever.processor, 'save_transcript') as mock_save:
                    mock_save.return_value = {fmt: temp_output_dir / f"test.{fmt}" for fmt in formats}

                    saved_files = retriever.save_transcript(video_intelligence, str(temp_output_dir), formats)

                    assert len(saved_files) == len(formats)
                    mock_save.assert_called_with(video_intelligence, str(temp_output_dir), formats)

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test error recovery and resilience in the workflow."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        # Test scenario: First video fails, second succeeds
        failed_video = comprehensive_video_metadata
        successful_video = VideoMetadata(
            video_id="recovery_test",
            url="https://www.youtube.com/watch?v=recovery_test",
            title="Recovery Test Video",
            channel="ClipScribe Testing",
            channel_id="clipscribe_testing",
            published_at=datetime.now(),
            duration=600,
            view_count=10000,
            description="Recovery test video",
            tags=["recovery"]
        )

        with patch.object(retriever.processor.downloader, 'search_videos', return_value=[failed_video, successful_video]), \
             patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:

            # First call fails, second succeeds
            mock_process.side_effect = [
                None,  # First video fails
                create_mock_video_intelligence()  # Second video succeeds
            ]

            results = await retriever.search("error recovery test", max_results=2)

            # Should have 1 successful result
            assert len(results) == 1
            assert results[0] is not None

            # Should have attempted both videos
            assert mock_process.call_count == 2

    @pytest.mark.asyncio
    async def test_performance_workflow(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test performance characteristics of the workflow."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = create_mock_video_intelligence()

            # Time the processing
            import time
            start_time = time.time()

            # Process multiple videos sequentially
            for i in range(5):
                await retriever.process_url(f"https://www.youtube.com/watch?v=perf_test_{i}")

            end_time = time.time()
            processing_time = end_time - start_time

            # Should complete within reasonable time (allowing for async processing)
            assert processing_time < 10  # 10 seconds for 5 videos

            # Verify stats accuracy
            stats = retriever.get_stats()
            assert stats["videos_processed"] == 5
            assert "average_cost" in stats

    @pytest.mark.asyncio
    async def test_chimera_compatibility_workflow(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test Chimera-compatible interface workflow."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process, \
             patch.object(retriever.processor.output_formatter, '_to_chimera_format') as mock_chimera:

            mock_video = create_mock_video_intelligence()
            mock_process.return_value = mock_video
            mock_chimera.return_value = {
                "type": "video",
                "source": "video_intelligence",
                "url": comprehensive_video_metadata.url,
                "title": comprehensive_video_metadata.title,
                "content": comprehensive_transcription_analysis["transcript"],
                "summary": comprehensive_transcription_analysis["summary"]
            }

            # Test retrieve method (Chimera-compatible)
            results = await retriever.retrieve("https://www.youtube.com/watch?v=chimera_test")

            assert len(results) == 1
            assert results[0]["type"] == "video"
            assert results[0]["source"] == "video_intelligence"
            assert "content" in results[0]
            assert "summary" in results[0]

            mock_process.assert_called_once_with("https://www.youtube.com/watch?v=chimera_test")
            mock_chimera.assert_called_once()

    def test_output_validation_workflow(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test output file validation and completeness."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        # Create a mock video intelligence result
        video_intelligence = create_mock_video_intelligence()
        video_intelligence.metadata = comprehensive_video_metadata
        video_intelligence.transcript.full_text = comprehensive_transcription_analysis["transcript"]
        video_intelligence.entities = comprehensive_transcription_analysis["entities"]
        video_intelligence.relationships = comprehensive_transcription_analysis["relationships"]

        # Test save_all_formats and validate output files
        with patch.object(retriever.processor, 'save_all_formats') as mock_save:
            expected_files = {
                "transcript_txt": temp_output_dir / "transcript.txt",
                "transcript_json": temp_output_dir / "transcript.json",
                "metadata": temp_output_dir / "metadata.json",
                "entities": temp_output_dir / "entities.json",
                "relationships": temp_output_dir / "relationships.json",
                "knowledge_graph": temp_output_dir / "knowledge_graph.json",
                "report": temp_output_dir / "report.md",
                "manifest": temp_output_dir / "manifest.json"
            }

            mock_save.return_value = expected_files

            saved_files = retriever.save_all_formats(video_intelligence, str(temp_output_dir))

            # Verify all expected files are present
            assert len(saved_files) >= 8
            assert "transcript_txt" in saved_files
            assert "transcript_json" in saved_files
            assert "metadata" in saved_files
            assert "entities" in saved_files
            assert "relationships" in saved_files
            assert "report" in saved_files

            mock_save.assert_called_once_with(video_intelligence, str(temp_output_dir), True)

    @pytest.mark.asyncio
    async def test_memory_efficiency_workflow(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test memory efficiency during processing."""
        import psutil
        import os

        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=False,  # Disable heavy extraction for memory test
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = create_mock_video_intelligence()

            # Process multiple videos
            for i in range(10):
                await retriever.process_url(f"https://www.youtube.com/watch?v=memory_test_{i}")

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100, f"Memory increased by {memory_increase}MB, which may indicate a leak"

            # Verify all processing completed
            stats = retriever.get_stats()
            assert stats["videos_processed"] == 10

    @pytest.mark.asyncio
    async def test_cross_platform_compatibility(self, comprehensive_video_metadata, comprehensive_transcription_analysis, temp_output_dir):
        """Test processing videos from different platforms."""
        retriever = VideoIntelligenceRetriever(
            cache_dir=str(temp_output_dir / "cache"),
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir=str(temp_output_dir)
        )

        # Test different platform URLs
        test_urls = [
            "https://www.youtube.com/watch?v=platform_test_1",
            "https://vimeo.com/123456789",
            "https://www.dailymotion.com/video/x1234567",
            "https://www.tiktok.com/@user/video/1234567890123456789"
        ]

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = create_mock_video_intelligence()

            for url in test_urls:
                result = await retriever.process_url(url)
                assert result is not None

            assert mock_process.call_count == len(test_urls)

            # Verify stats reflect all platforms
            stats = retriever.get_stats()
            assert stats["videos_processed"] == len(test_urls)
