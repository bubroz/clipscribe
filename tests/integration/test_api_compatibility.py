"""API compatibility and Chimera interface tests."""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript


@pytest.mark.integration
class TestAPICompatibility:
    """Test API compatibility and interface contracts."""

    @pytest.fixture
    def video_retriever(self):
        """Create a VideoIntelligenceRetriever for API testing."""
        return VideoIntelligenceRetriever(
            cache_dir="tests/cache",
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,
            output_dir="tests/output"
        )

    @pytest.fixture
    def mock_video_intelligence(self):
        """Create mock VideoIntelligence for API testing."""
        metadata = VideoMetadata(
            video_id="api_test_123",
            url="https://www.youtube.com/watch?v=api_test",
            title="API Compatibility Test Video",
            channel="API Testing Channel",
            channel_id="api_testing",
            published_at=None,
            duration=300,
            view_count=1000,
            description="Test video for API compatibility",
            tags=["api", "test"]
        )

        transcript = VideoTranscript(
            full_text="This is a test transcript for API compatibility testing.",
            segments=[
                {"text": "This is a test transcript", "start": 0.0, "end": 5.0},
                {"text": "for API compatibility testing.", "start": 5.0, "end": 10.0}
            ]
        )

        return VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="API compatibility test summary",
            entities=[],
            relationships=[],
            key_points=[],
            topics=[],
            processing_cost=0.25
        )

    def test_public_interface_contract(self, video_retriever):
        """Test that the public interface matches expected contract."""
        # Verify all expected public methods exist
        expected_methods = [
            'process_url',
            'search',
            'save_transcript',
            'save_all_formats',
            'get_saved_files',
            'get_stats',
            'retrieve'
        ]

        for method_name in expected_methods:
            assert hasattr(video_retriever, method_name), f"Missing public method: {method_name}"
            assert callable(getattr(video_retriever, method_name)), f"Method {method_name} is not callable"

    @pytest.mark.asyncio
    async def test_chimera_compatible_interface(self, video_retriever, mock_video_intelligence):
        """Test Chimera-compatible output format."""
        with patch.object(video_retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_video_intelligence

            # Test retrieve method (should return Chimera-compatible format)
            results = await video_retriever.retrieve("https://www.youtube.com/watch?v=chimera_test")

            assert len(results) == 1
            result = results[0]

            # Verify Chimera format structure
            expected_chimera_fields = ['type', 'source', 'url', 'title', 'content', 'summary']
            for field in expected_chimera_fields:
                assert field in result, f"Missing Chimera field: {field}"

            assert result['type'] == 'video'
            assert result['source'] == 'video_intelligence'
            assert result['url'] == mock_video_intelligence.metadata.url
            assert result['title'] == mock_video_intelligence.metadata.title
            assert result['content'] == mock_video_intelligence.transcript.full_text
            assert result['summary'] == mock_video_intelligence.summary

    def test_chimera_format_with_complex_data(self, video_retriever):
        """Test Chimera format with complex video intelligence data."""
        # Create complex video intelligence
        metadata = VideoMetadata(
            video_id="complex_chimera",
            url="https://www.youtube.com/watch?v=complex",
            title="Complex Chimera Test",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=None,
            duration=600,
            view_count=50000,
            description="Complex test with entities and relationships",
            tags=["complex", "chimera"]
        )

        transcript = VideoTranscript(
            full_text="Complex transcript with multiple entities and relationships.",
            segments=[{"text": "Complex transcript", "start": 0.0, "end": 10.0}]
        )

        video_intel = VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary="Complex summary with detailed analysis",
            entities=[
                {"name": "Entity1", "type": "PERSON", "confidence": 0.9},
                {"name": "Entity2", "type": "ORGANIZATION", "confidence": 0.8}
            ],
            relationships=[
                {
                    "subject": "Entity1",
                    "predicate": "works_at",
                    "object": "Entity2",
                    "confidence": 0.85
                }
            ],
            key_points=[
                {"text": "Key point 1", "importance": 0.9},
                {"text": "Key point 2", "importance": 0.8}
            ],
            topics=["technology", "business"],
            processing_cost=0.40
        )

        chimera_data = video_retriever.processor.output_formatter._to_chimera_format(video_intel)

        # Verify complex data is preserved
        assert chimera_data['title'] == "Complex Chimera Test"
        assert chimera_data['content'] == "Complex transcript with multiple entities and relationships."
        assert chimera_data['summary'] == "Complex summary with detailed analysis"
        assert 'metadata' in chimera_data
        assert chimera_data['metadata']['duration'] == 600
        assert chimera_data['metadata']['view_count'] == 50000

    @pytest.mark.asyncio
    async def test_search_api_compatibility(self, video_retriever):
        """Test search API compatibility."""
        with patch.object(video_retriever.processor.downloader, 'search_videos', return_value=[]) as mock_search:
            # Test search method signature and return type
            results = await video_retriever.search("test query", max_results=5)

            assert isinstance(results, list), "Search should return a list"
            mock_search.assert_called_once_with("test query", 5, "youtube")

    def test_save_methods_api_compatibility(self, video_retriever, mock_video_intelligence):
        """Test save method API compatibility."""
        with patch.object(video_retriever.processor, 'save_transcript') as mock_save_transcript, \
             patch.object(video_retriever.processor, 'save_all_formats') as mock_save_all:

            mock_save_transcript.return_value = {"txt": "/path/to/transcript.txt"}
            mock_save_all.return_value = {"json": "/path/to/video.json"}

            # Test save_transcript signature
            result1 = video_retriever.save_transcript(mock_video_intelligence, "output_dir", ["txt"])
            assert isinstance(result1, dict)
            mock_save_transcript.assert_called_once_with(mock_video_intelligence, "output_dir", ["txt"])

            # Test save_all_formats signature
            result2 = video_retriever.save_all_formats(mock_video_intelligence, "output_dir", True)
            assert isinstance(result2, dict)
            mock_save_all.assert_called_once_with(mock_video_intelligence, "output_dir", True)

    def test_get_stats_api_compatibility(self, video_retriever):
        """Test get_stats API compatibility."""
        with patch.object(video_retriever.processor, 'get_stats') as mock_stats:
            mock_stats.return_value = {"videos_processed": 0, "total_cost": 0.0}

            stats = video_retriever.get_stats()

            assert isinstance(stats, dict), "get_stats should return a dict"
            assert "videos_processed" in stats, "Stats should include videos_processed"
            assert "total_cost" in stats, "Stats should include total_cost"

    def test_get_saved_files_api_compatibility(self, video_retriever, mock_video_intelligence):
        """Test get_saved_files API compatibility."""
        with patch('clipscribe.retrievers.video_retriever.create_output_structure') as mock_create:
            mock_create.return_value = {"txt": "/path/to/transcript.txt"}

            result = video_retriever.get_saved_files(mock_video_intelligence, "output_dir")

            assert isinstance(result, dict), "get_saved_files should return a dict"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_method_api_compatibility(self, video_retriever):
        """Test retrieve method API compatibility."""
        with patch.object(video_retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process, \
             patch.object(video_retriever.processor.output_formatter, '_to_chimera_format') as mock_chimera:

            mock_process.return_value = mock_video_intelligence
            mock_chimera.return_value = {"type": "video", "content": "test"}

            # Test retrieve with URL
            results = await video_retriever.retrieve("https://www.youtube.com/watch?v=test")
            assert isinstance(results, list), "retrieve should return a list"

            # Test retrieve with search query
            with patch.object(video_retriever.processor.downloader, 'search_videos', return_value=[mock_video_intelligence.metadata]):
                search_results = await video_retriever.retrieve("search query", max_results=1)
                assert isinstance(search_results, list), "retrieve with search should return a list"

    def test_error_handling_api_compatibility(self, video_retriever):
        """Test error handling maintains API compatibility."""
        with patch.object(video_retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = None

            # Should handle errors gracefully and maintain return type contract
            import asyncio
            result = asyncio.run(video_retriever.process_url("invalid_url"))

            # API should still return expected type even on error
            assert result is None  # This is the expected return type for failures

    def test_parameter_defaults_compatibility(self, video_retriever):
        """Test that parameter defaults maintain backward compatibility."""
        # Test that methods work with minimal parameters
        try:
            stats = video_retriever.get_stats()
            assert isinstance(stats, dict)
        except Exception as e:
            pytest.fail(f"get_stats() should work with no parameters: {e}")

        try:
            saved_files = video_retriever.get_saved_files(mock_video_intelligence)
            assert isinstance(saved_files, dict)
        except Exception as e:
            pytest.fail(f"get_saved_files() should work with minimal parameters: {e}")

    def test_output_format_compatibility(self, video_retriever, mock_video_intelligence, temp_output_dir):
        """Test that output formats are compatible with expected interfaces."""
        with patch.object(video_retriever.processor, 'save_all_formats') as mock_save:
            expected_files = {
                "transcript.txt": temp_output_dir / "transcript.txt",
                "transcript.json": temp_output_dir / "transcript.json",
                "metadata.json": temp_output_dir / "metadata.json",
                "entities.json": temp_output_dir / "entities.json",
                "relationships.json": temp_output_dir / "relationships.json",
                "report.md": temp_output_dir / "report.md"
            }

            mock_save.return_value = expected_files

            # Save files using the API
            saved_files = video_retriever.save_all_formats(mock_video_intelligence, str(temp_output_dir))

            # Verify return type and structure
            assert isinstance(saved_files, dict), "save_all_formats should return a dict"
            assert len(saved_files) > 0, "Should return at least one file path"

            # Verify file paths are Path objects or strings
            for path in saved_files.values():
                assert isinstance(path, (str, Path)), f"File path should be string or Path, got {type(path)}"

    @pytest.mark.asyncio
    async def test_concurrent_api_calls_compatibility(self, video_retriever):
        """Test that the API handles concurrent calls correctly."""
        import asyncio

        async def api_call(url):
            """Make an API call and return result."""
            return await video_retriever.process_url(url)

        # Make multiple concurrent API calls
        urls = [
            "https://www.youtube.com/watch?v=test1",
            "https://www.youtube.com/watch?v=test2",
            "https://www.youtube.com/watch?v=test3"
        ]

        with patch.object(video_retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_video_intelligence

            tasks = [api_call(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All calls should complete without API contract violations
            assert len(results) == 3, "All concurrent calls should complete"

            # Results should be of expected type (either VideoIntelligence or None)
            for result in results:
                assert result is None or isinstance(result, VideoIntelligence), f"Unexpected result type: {type(result)}"

    def test_stats_tracking_api_compatibility(self, video_retriever):
        """Test that stats tracking maintains API compatibility."""
        # Get initial stats
        initial_stats = video_retriever.get_stats()

        # Verify stats structure
        required_fields = ["videos_processed", "total_cost"]
        for field in required_fields:
            assert field in initial_stats, f"Stats should include {field}"
            assert isinstance(initial_stats[field], (int, float)), f"{field} should be numeric"

        # Stats should be non-negative
        assert initial_stats["videos_processed"] >= 0, "videos_processed should be non-negative"
        assert initial_stats["total_cost"] >= 0, "total_cost should be non-negative"

    def test_file_path_return_type_compatibility(self, video_retriever, mock_video_intelligence):
        """Test that file path return types are consistent."""
        with patch.object(video_retriever.processor, 'save_transcript') as mock_save:
            # Test with Path objects
            path_objects = {
                "txt": Path("/path/to/transcript.txt"),
                "json": Path("/path/to/transcript.json")
            }
            mock_save.return_value = path_objects

            result = video_retriever.save_transcript(mock_video_intelligence, "output", ["txt", "json"])

            # Should handle Path objects
            assert isinstance(result, dict)
            for path in result.values():
                assert isinstance(path, (str, Path))

    def test_empty_results_api_compatibility(self, video_retriever):
        """Test API compatibility when no results are returned."""
        with patch.object(video_retriever.processor.downloader, 'search_videos', return_value=[]):
            # Search with no results
            results = asyncio.run(video_retriever.search("nonexistent_query"))
            assert isinstance(results, list), "Empty search should return a list"
            assert len(results) == 0, "Empty search should return empty list"

    def test_large_data_api_compatibility(self, video_retriever):
        """Test API compatibility with large amounts of data."""
        # Create video intelligence with large amounts of data
        large_transcript = "Large transcript content. " * 1000
        large_summary = "Large summary content. " * 500

        large_metadata = VideoMetadata(
            video_id="large_test",
            url="https://www.youtube.com/watch?v=large",
            title="Large Data Test",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=None,
            duration=3600,
            view_count=1000000,
            description="Large description content. " * 100,
            tags=["large"] * 50
        )

        large_video_intel = VideoIntelligence(
            metadata=large_metadata,
            transcript=VideoTranscript(full_text=large_transcript, segments=[]),
            summary=large_summary,
            entities=[{"name": f"Entity{i}", "type": "PERSON"} for i in range(1000)],
            relationships=[{
                "subject": f"Entity{i}",
                "predicate": "related_to",
                "object": f"Entity{i+1}"
            } for i in range(999)],
            key_points=[{"text": f"Key point {i}"} for i in range(100)],
            topics=["topic"] * 100,
            processing_cost=1.50
        )

        # Test that API can handle large data structures
        with patch.object(video_retriever.processor, 'save_all_formats') as mock_save:
            mock_save.return_value = {"large_output": Path("/path/to/large_output.json")}

            result = video_retriever.save_all_formats(large_video_intel, "output_dir")

            # Should handle large data without API contract violations
            assert isinstance(result, dict), "Should return dict even with large data"

    @pytest.mark.asyncio
    async def test_api_resilience_to_network_issues(self, video_retriever):
        """Test API resilience to network issues."""
        # Test various network-related error conditions
        error_conditions = [
            ("connection_timeout", Exception("Connection timeout")),
            ("dns_resolution", Exception("DNS resolution failed")),
            ("server_error", Exception("Server returned 500")),
            ("rate_limit", Exception("Rate limit exceeded"))
        ]

        for error_name, error in error_conditions:
            with patch.object(video_retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
                mock_process.side_effect = error

                # API should handle errors gracefully
                try:
                    result = await video_retriever.process_url("https://www.youtube.com/watch?v=error_test")
                    # Should return None or raise a handled exception
                    assert result is None or isinstance(result, Exception), f"Unexpected result for {error_name}: {result}"
                except Exception as e:
                    # If exception is raised, it should be the expected error
                    assert str(e) == str(error), f"Unexpected error message for {error_name}"

    def test_api_version_compatibility(self, video_retriever):
        """Test API version compatibility markers."""
        # Verify that the API includes version information where expected
        stats = video_retriever.get_stats()

        # Stats should include some version or compatibility markers
        assert isinstance(stats, dict), "Stats should be a dict for version compatibility"

        # The exact fields may evolve, but the structure should be stable
        assert len(stats) >= 2, "Stats should include multiple compatibility fields"
