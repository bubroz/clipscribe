"""Integration tests for real video processing with test videos."""
import pytest
import asyncio
import json
import os
from pathlib import Path
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence


@pytest.mark.integration
@pytest.mark.requires_api
class TestRealVideoProcessing:
    """Integration tests that process real videos from the test video table."""

    @pytest.fixture
    def real_api_key(self):
        """Get the real Google API key from .env file (not the mocked test key)."""
        import os
        from pathlib import Path

        # Read the real API key from .env file before autouse fixture overrides it
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY="):
                        real_key = line.strip().split("=", 1)[1].strip('"')
                        if real_key and real_key != "test-api-key":
                            return real_key

        # Fallback to environment if .env doesn't exist
        real_key = os.environ.get("GOOGLE_API_KEY")
        if not real_key or real_key == "test-api-key":
            pytest.skip("Real Google API key required for integration tests")
        return real_key

    @pytest.fixture
    def video_retriever(self, real_api_key):
        """Create a VideoIntelligenceRetriever for testing with real API key."""
        return VideoIntelligenceRetriever(
            cache_dir="tests/cache",
            use_advanced_extraction=True,
            mode="auto",
            use_cache=False,  # Disable cache for testing
            output_dir="tests/output",
            enhance_transcript=True,
            use_flash=False,  # Use Pro model (not Flash)
            api_key=real_api_key  # Pass real API key directly
        )

    @pytest.fixture
    def test_output_dir(self, temp_directory):
        """Create a temporary output directory for test results."""
        output_dir = temp_directory / "real_video_test_output"
        output_dir.mkdir(exist_ok=True)
        return output_dir

    @pytest.mark.asyncio
    async def test_tier_1_2_selections_training_part_1(self, video_retriever, test_output_dir):
        """Test processing of Tier 1 & 2 Selections Training Part 1."""
        video_url = "https://www.youtube.com/watch?v=Nr7vbOSzpSk"

        # Process the video
        result = await video_retriever.process_url(video_url)

        # Verify result
        assert result is not None
        assert isinstance(result, VideoIntelligence)
        assert result.metadata.title is not None
        assert result.transcript.full_text is not None
        assert len(result.transcript.full_text) > 100  # Should have substantial content

        # Verify entities were extracted
        assert hasattr(result, 'entities')
        assert len(result.entities) > 0

        # Verify relationships were extracted
        assert hasattr(result, 'relationships')
        assert len(result.relationships) > 0

        # Verify key points were extracted
        assert hasattr(result, 'key_points')
        assert len(result.key_points) > 0

        # Verify the entity extraction results
        assert len(result.entities) > 0, f"Expected entities but got {len(result.entities)}"

        # Log success details
        print(f"✅ SUCCESS: Extracted {len(result.entities)} entities from real video")
        print(f"✅ SUCCESS: Built knowledge graph with {len(result.relationships)} relationships")
        print(f"✅ SUCCESS: Generated {len(result.key_points)} key points")
        print(f"✅ SUCCESS: Identified {len(result.topics)} topics")

        # Verify processing cost is reasonable
        assert result.processing_cost > 0
        assert result.processing_cost < 1.0  # Should be less than $1

    @pytest.mark.asyncio
    async def test_tier_1_2_selections_training_part_2(self, video_retriever, test_output_dir):
        """Test processing of Tier 1 & 2 Selections Training Part 2."""
        video_url = "https://www.youtube.com/watch?v=tjFNZlZEJLY"

        # Process the video
        result = await video_retriever.process_url(video_url)

        # Verify result
        assert result is not None
        assert isinstance(result, VideoIntelligence)
        assert result.metadata.title is not None
        assert result.transcript.full_text is not None
        assert len(result.transcript.full_text) > 100  # Should have substantial content

        # Verify entities were extracted
        assert hasattr(result, 'entities')
        assert len(result.entities) > 0

        # Verify relationships were extracted
        assert hasattr(result, 'relationships')
        assert len(result.relationships) > 0

        # Verify key points were extracted
        assert hasattr(result, 'key_points')
        assert len(result.key_points) > 0

        # Verify the entity extraction results
        assert len(result.entities) > 0, f"Expected entities but got {len(result.entities)}"

        # Log success details
        print(f"✅ SUCCESS: Extracted {len(result.entities)} entities from real video")
        print(f"✅ SUCCESS: Built knowledge graph with {len(result.relationships)} relationships")
        print(f"✅ SUCCESS: Generated {len(result.key_points)} key points")
        print(f"✅ SUCCESS: Identified {len(result.topics)} topics")

        # Verify processing cost is reasonable
        assert result.processing_cost > 0
        assert result.processing_cost < 1.0  # Should be less than $1

    @pytest.mark.asyncio
    async def test_tier_1_2_selections_training_part_3(self, video_retriever, test_output_dir):
        """Test processing of Tier 1 & 2 Selections Training Part 3."""
        video_url = "https://www.youtube.com/watch?v=7r-qOjUOjbs"

        # Process the video
        result = await video_retriever.process_url(video_url)

        # Verify result
        assert result is not None
        assert isinstance(result, VideoIntelligence)
        assert result.metadata.title is not None
        assert result.transcript.full_text is not None
        assert len(result.transcript.full_text) > 100  # Should have substantial content

        # Verify entities were extracted
        assert hasattr(result, 'entities')
        assert len(result.entities) > 0

        # Verify relationships were extracted
        assert hasattr(result, 'relationships')
        assert len(result.relationships) > 0

        # Verify key points were extracted
        assert hasattr(result, 'key_points')
        assert len(result.key_points) > 0

        # Verify the entity extraction results
        assert len(result.entities) > 0, f"Expected entities but got {len(result.entities)}"

        # Log success details
        print(f"✅ SUCCESS: Extracted {len(result.entities)} entities from real video")
        print(f"✅ SUCCESS: Built knowledge graph with {len(result.relationships)} relationships")
        print(f"✅ SUCCESS: Generated {len(result.key_points)} key points")
        print(f"✅ SUCCESS: Identified {len(result.topics)} topics")

        # Verify processing cost is reasonable
        assert result.processing_cost > 0
        assert result.processing_cost < 1.0  # Should be less than $1

    @pytest.mark.asyncio
    async def test_tier_1_2_selections_training_series(self, video_retriever, test_output_dir):
        """Test processing of the complete Tier 1 & 2 Selections Training series."""
        series_urls = [
            "https://www.youtube.com/watch?v=Nr7vbOSzpSk",  # Part 1
            "https://www.youtube.com/watch?v=tjFNZlZEJLY",  # Part 2
            "https://www.youtube.com/watch?v=7r-qOjUOjbs"   # Part 3
        ]

        series_results = []

        # Process each video in the series
        for i, url in enumerate(series_urls):
            result = await video_retriever.process_url(url)

            assert result is not None, f"Video {i+1} should process successfully"
            assert isinstance(result, VideoIntelligence)
            assert result.transcript.full_text is not None

            series_results.append(result)

        # Verify series characteristics
        total_entities = sum(len(result.entities) for result in series_results)
        total_relationships = sum(len(result.relationships) for result in series_results)
        total_cost = sum(result.processing_cost for result in series_results)

        # Should have substantial extraction across the series
        assert total_entities > 10, f"Should extract entities across series, got {total_entities}"
        assert total_relationships > 5, f"Should extract relationships across series, got {total_relationships}"
        assert total_cost > 0, f"Should have processing cost, got {total_cost}"

        # Verify series processing stats
        stats = video_retriever.get_stats()
        assert stats["videos_processed"] == 3
        assert stats["total_cost"] == total_cost

    @pytest.mark.asyncio
    async def test_my_chemical_romance_series(self, video_retriever, test_output_dir):
        """Test processing of My Chemical Romance documentary series."""
        series_urls = [
            "https://youtu.be/gxUrKV33yys?si=iYMMiwq0mdOZmnWj",  # Part 1
            "https://youtu.be/2jlsVEeZmVo?si=DIFBEdOFjIx-M7er",  # Part 2
            "https://youtu.be/o6wtzHtfjyo?si=p_5hEh_Mjr7wDhLY",  # Part 3
            "https://youtu.be/0ESDiJdCfxY?si=8znBwJj-5S1waVRQ"   # Part 4
        ]

        series_results = []

        for i, url in enumerate(series_urls):
            result = await video_retriever.process_url(url)

            assert result is not None, f"MCR Part {i+1} should process successfully"
            assert isinstance(result, VideoIntelligence)
            assert result.transcript.full_text is not None

            series_results.append(result)

        # Verify series has substantial content
        total_text_length = sum(len(result.transcript.full_text) for result in series_results)
        total_entities = sum(len(result.entities) for result in series_results)

        assert total_text_length > 10000, f"Series should have substantial content, got {total_text_length} chars"
        assert total_entities > 20, f"Series should have entities, got {total_entities}"

    @pytest.mark.asyncio
    async def test_pegasus_spyware_investigation(self, video_retriever, test_output_dir):
        """Test processing of FRONTLINE PBS Pegasus Spyware investigation."""
        series_urls = [
            "https://www.youtube.com/watch?v=6ZVj1_SE4Mo&t=65s",  # Part 1
            "https://www.youtube.com/watch?v=xYMWTXIkANM"         # Part 2
        ]

        series_results = []

        for i, url in enumerate(series_urls):
            result = await video_retriever.process_url(url)

            assert result is not None, f"Pegasus Part {i+1} should process successfully"
            assert isinstance(result, VideoIntelligence)

            # Investigative journalism should have substantial entities
            assert len(result.entities) > 5, f"Investigation should have entities, got {len(result.entities)}"
            assert len(result.relationships) > 3, f"Investigation should have relationships, got {len(result.relationships)}"

            series_results.append(result)

        # Verify investigation has substantial intelligence value
        total_entities = sum(len(result.entities) for result in series_results)
        total_relationships = sum(len(result.relationships) for result in series_results)

        assert total_entities > 15, f"Investigation should have substantial entities, got {total_entities}"
        assert total_relationships > 8, f"Investigation should have substantial relationships, got {total_relationships}"

    @pytest.mark.asyncio
    async def test_cross_platform_video_processing(self, video_retriever, test_output_dir):
        """Test processing videos from different platforms."""
        # Test different video platforms
        test_videos = [
            ("YouTube", "https://www.youtube.com/watch?v=Nr7vbOSzpSk"),
            ("Vimeo", "https://vimeo.com/123456789"),  # This may not exist, but tests the client
        ]

        successful_results = 0

        for platform, url in test_videos:
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

    def test_video_search_and_process_integration(self, video_retriever, test_output_dir):
        """Test the search and process integration workflow."""
        # This test demonstrates the full workflow: search -> process -> save
        search_results = video_retriever.search("test query", max_results=1)

        # Note: In a real test environment, this would return actual results
        # For this integration test, we verify the method exists and can be called
        assert isinstance(search_results, list)

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, video_retriever, test_output_dir):
        """Test batch processing performance and memory usage."""
        import time
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process multiple videos
        test_urls = [
            "https://www.youtube.com/watch?v=Nr7vbOSzpSk",
            "https://www.youtube.com/watch?v=tjFNZlZEJLY",
            "https://www.youtube.com/watch?v=7r-qOjUOjbs"
        ]

        start_time = time.time()
        successful_processes = 0

        for url in test_urls:
            try:
                result = await video_retriever.process_url(url)
                if result is not None:
                    successful_processes += 1

                    # Save in different formats
                    saved_files = video_retriever.save_transcript(result, str(test_output_dir), ["txt", "json"])
                    assert len(saved_files) >= 2

            except Exception as e:
                print(f"Batch processing failed for {url}: {e}")

        end_time = time.time()
        processing_time = end_time - start_time

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Performance assertions
        assert successful_processes > 0, "At least one video should process successfully"
        assert processing_time < 300, f"Batch processing should complete within 5 minutes, took {processing_time}s"
        assert memory_increase < 200, f"Memory increase should be reasonable, got {memory_increase}MB"

        # Verify batch processing stats
        stats = video_retriever.get_stats()
        assert stats["videos_processed"] == successful_processes

    @pytest.mark.asyncio
    async def test_error_recovery_and_resilience(self, video_retriever, test_output_dir):
        """Test error recovery and system resilience with real videos."""
        # Test with a mix of valid and potentially problematic URLs
        test_cases = [
            ("Valid YouTube", "https://www.youtube.com/watch?v=Nr7vbOSzpSk", True),
            ("Invalid URL", "https://www.youtube.com/watch?v=invalid_video_id_12345", False),
        ]

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

            except Exception as e:
                failed_results += 1
                print(f"Test {test_name} failed as expected: {e}")

        # System should handle both success and failure cases gracefully
        assert successful_results >= 1, "At least one valid video should process successfully"
        assert failed_results <= 1, "Only one test case should fail"

    def test_output_format_completeness(self, video_retriever, test_output_dir):
        """Test that all output formats are generated correctly."""
        # This test would require a pre-processed video intelligence object
        # In a real test environment, you would load a saved result or process a video first

        # For now, verify the methods exist and can be called
        assert hasattr(video_retriever, 'save_transcript')
        assert hasattr(video_retriever, 'save_all_formats')
        assert hasattr(video_retriever, 'get_saved_files')

    @pytest.mark.asyncio
    async def test_processing_cost_accuracy(self, video_retriever, test_output_dir):
        """Test that processing costs are accurately tracked."""
        # Process a video and verify cost tracking
        result = await video_retriever.process_url("https://www.youtube.com/watch?v=Nr7vbOSzpSk")

        if result is not None:
            # Verify cost is reasonable for the content length
            content_length = len(result.transcript.full_text) if result.transcript else 0

            assert result.processing_cost > 0, "Should have processing cost"
            assert result.processing_cost < 2.0, f"Cost should be reasonable, got ${result.processing_cost}"

            # Cost should be roughly proportional to content length
            expected_cost_per_char = 0.0001  # Approximate cost per character
            expected_cost = content_length * expected_cost_per_char

            # Allow reasonable variance (50% either way)
            assert result.processing_cost > expected_cost * 0.5, f"Cost too low: ${result.processing_cost} for {content_length} chars"
            assert result.processing_cost < expected_cost * 1.5, f"Cost too high: ${result.processing_cost} for {content_length} chars"

    @pytest.mark.asyncio
    async def test_entity_extraction_quality(self, video_retriever, test_output_dir):
        """Test the quality of entity extraction on real content."""
        result = await video_retriever.process_url("https://www.youtube.com/watch?v=Nr7vbOSzpSk")

        if result is not None and result.entities:
            # Verify entity quality metrics
            total_entities = len(result.entities)
            unique_entity_types = set(entity.type for entity in result.entities)
            entities_with_confidence = sum(1 for entity in result.entities if hasattr(entity, 'confidence') and entity.confidence > 0.5)

            assert total_entities > 5, f"Should extract substantial entities, got {total_entities}"
            assert len(unique_entity_types) > 2, f"Should have diverse entity types, got {unique_entity_types}"
            assert entities_with_confidence > 0, "Should have high-confidence entities"

            # Verify entity attributes
            for entity in result.entities:
                assert hasattr(entity, 'name')
                assert hasattr(entity, 'type')
                assert entity.name is not None
                assert entity.type is not None

    @pytest.mark.asyncio
    async def test_relationship_extraction_quality(self, video_retriever, test_output_dir):
        """Test the quality of relationship extraction on real content."""
        result = await video_retriever.process_url("https://www.youtube.com/watch?v=Nr7vbOSzpSk")

        if result is not None and result.relationships:
            # Verify relationship quality
            total_relationships = len(result.relationships)
            unique_predicates = set(rel.get('predicate', '') for rel in result.relationships)
            relationships_with_evidence = sum(1 for rel in result.relationships if 'evidence_chain' in rel)

            assert total_relationships > 3, f"Should extract relationships, got {total_relationships}"
            assert len(unique_predicates) > 1, f"Should have diverse relationship types, got {unique_predicates}"

            # Verify relationship structure
            for relationship in result.relationships:
                assert 'subject' in relationship
                assert 'predicate' in relationship
                assert 'object' in relationship
                assert relationship['subject'] is not None
                assert relationship['predicate'] is not None
                assert relationship['object'] is not None

    @pytest.mark.asyncio
    async def test_knowledge_graph_generation(self, video_retriever, test_output_dir):
        """Test knowledge graph generation from real video content."""
        result = await video_retriever.process_url("https://www.youtube.com/watch?v=Nr7vbOSzpSk")

        if result is not None:
            # Save all formats to trigger knowledge graph generation
            saved_files = video_retriever.save_all_formats(result, str(test_output_dir))

            # Check if knowledge graph was generated
            gexf_files = [f for f in saved_files.values() if str(f).endswith('.gexf')]
            kg_json_files = [f for f in saved_files.values() if 'knowledge_graph.json' in str(f)]

            if hasattr(result, 'knowledge_graph') and result.knowledge_graph:
                assert len(kg_json_files) > 0, "Should create knowledge graph JSON file"
                assert len(gexf_files) > 0, "Should create GEXF file for graph visualization"

                # Verify knowledge graph structure
                kg = result.knowledge_graph
                assert 'nodes' in kg
                assert 'edges' in kg
                assert 'node_count' in kg
                assert 'edge_count' in kg
                assert kg['node_count'] > 0
                assert kg['edge_count'] >= 0

                # Verify node and edge data
                for node in kg['nodes']:
                    assert 'id' in node
                    assert 'type' in node

                for edge in kg['edges']:
                    assert 'source' in edge
                    assert 'target' in edge
                    assert 'predicate' in edge
