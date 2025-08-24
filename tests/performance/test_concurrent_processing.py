"""Performance tests for concurrent video processing."""
import pytest
import asyncio
import time
import psutil
import os
from concurrent.futures import ThreadPoolExecutor
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever


@pytest.fixture(autouse=True)
def skip_if_no_api_key():
    """Skip performance tests if no real API key is available."""
    import os
    if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "test-api-key":
        pytest.skip("Performance tests require a real GOOGLE_API_KEY environment variable")


@pytest.mark.performance
class TestConcurrentProcessingPerformance:
    """Performance tests for concurrent video processing operations."""

    @pytest.fixture
    def video_retriever(self):
        """Create a VideoIntelligenceRetriever for performance testing."""
        return VideoIntelligenceRetriever(
            cache_dir="tests/cache",
            use_advanced_extraction=False,  # Disable heavy extraction for performance tests
            mode="auto",
            use_cache=False,
            output_dir="tests/output"
        )

    @pytest.fixture
    def test_videos(self):
        """Get a list of test videos for performance testing."""
        return [
            "https://www.youtube.com/watch?v=Nr7vbOSzpSk",  # Tier 1 & 2 Selections Part 1
            "https://www.youtube.com/watch?v=tjFNZlZEJLY",  # Tier 1 & 2 Selections Part 2
            "https://www.youtube.com/watch?v=7r-qOjUOjbs",  # Tier 1 & 2 Selections Part 3
        ]

    @pytest.mark.asyncio
    async def test_sequential_processing_baseline(self, video_retriever, test_videos):
        """Test sequential processing as baseline for performance comparison."""
        start_time = time.time()
        successful_processes = 0

        for url in test_videos:
            try:
                result = await video_retriever.process_url(url)
                if result is not None:
                    successful_processes += 1
            except Exception as e:
                print(f"Sequential processing failed for {url}: {e}")

        end_time = time.time()
        sequential_time = end_time - start_time

        # Verify results
        assert successful_processes > 0, "At least one video should process successfully"

        # Store metrics for comparison
        stats = video_retriever.get_stats()
        return {
            "sequential_time": sequential_time,
            "videos_processed": successful_processes,
            "stats": stats
        }

    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self, video_retriever, test_videos):
        """Test concurrent processing performance with asyncio.gather."""
        start_time = time.time()

        # Create tasks for concurrent processing
        tasks = [video_retriever.process_url(url) for url in test_videos]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        concurrent_time = end_time - start_time

        # Analyze results
        successful_processes = sum(1 for result in results if not isinstance(result, Exception) and result is not None)
        failed_processes = sum(1 for result in results if isinstance(result, Exception) or result is None)

        # Verify performance improvements
        assert successful_processes > 0, "At least one video should process successfully"

        # Concurrent processing should be faster than sequential for multiple videos
        if len(test_videos) > 1:
            # We expect some performance improvement, but allow for API rate limiting
            assert concurrent_time < (len(test_videos) * 60), f"Concurrent processing should complete within reasonable time, took {concurrent_time}s"

        return {
            "concurrent_time": concurrent_time,
            "videos_processed": successful_processes,
            "failed_processes": failed_processes,
            "stats": video_retriever.get_stats()
        }

    @pytest.mark.asyncio
    async def test_memory_usage_during_concurrent_processing(self, video_retriever, test_videos):
        """Test memory usage during concurrent processing."""
        process = psutil.Process(os.getpid())

        # Monitor memory before processing
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        peak_memory = initial_memory

        async def process_with_memory_monitoring(url):
            """Process a video while monitoring memory usage."""
            nonlocal peak_memory

            result = await video_retriever.process_url(url)

            # Check memory usage after each video
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            peak_memory = max(peak_memory, current_memory)

            return result

        # Process videos concurrently with memory monitoring
        tasks = [process_with_memory_monitoring(url) for url in test_videos]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        peak_memory_increase = peak_memory - initial_memory

        successful_processes = sum(1 for result in results if not isinstance(result, Exception) and result is not None)

        # Memory assertions
        assert successful_processes > 0, "At least one video should process successfully"
        assert memory_increase < 200, f"Memory increase should be reasonable, got {memory_increase}MB"
        assert peak_memory_increase < 300, f"Peak memory increase should be reasonable, got {peak_memory_increase}MB"

        return {
            "initial_memory": initial_memory,
            "final_memory": final_memory,
            "peak_memory": peak_memory,
            "memory_increase": memory_increase,
            "peak_memory_increase": peak_memory_increase,
            "videos_processed": successful_processes
        }

    @pytest.mark.asyncio
    async def test_rate_limiting_resilience(self, video_retriever):
        """Test system's resilience to API rate limiting."""
        # Test with a single video multiple times to potentially trigger rate limits
        test_url = "https://www.youtube.com/watch?v=Nr7vbOSzpSk"

        results = []
        start_time = time.time()

        # Attempt multiple rapid requests
        for i in range(3):
            try:
                result = await video_retriever.process_url(test_url)
                results.append(result)
                if i < 2:  # Don't wait after the last request
                    await asyncio.sleep(1)  # Small delay between requests
            except Exception as e:
                results.append(e)
                print(f"Request {i+1} failed: {e}")

        end_time = time.time()
        processing_time = end_time - start_time

        successful_results = sum(1 for result in results if not isinstance(result, Exception) and result is not None)

        # Should handle rate limiting gracefully
        assert successful_results > 0, "At least one request should succeed"
        assert processing_time < 120, f"Rate limit testing should complete within 2 minutes, took {processing_time}s"

        return {
            "successful_results": successful_results,
            "total_requests": len(results),
            "processing_time": processing_time
        }

    def test_thread_pool_performance_comparison(self, video_retriever, test_videos):
        """Compare asyncio performance with thread pool execution."""
        import concurrent.futures

        async def async_processing():
            """Process videos using asyncio."""
            start_time = time.time()
            tasks = [video_retriever.process_url(url) for url in test_videos]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            return end_time - start_time, results

        def sync_processing_wrapper(url):
            """Wrapper to run async processing in sync context."""
            return asyncio.run(video_retriever.process_url(url))

        def thread_processing():
            """Process videos using thread pool."""
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=3) as executor:
                results = list(executor.map(sync_processing_wrapper, test_videos))
            end_time = time.time()
            return end_time - start_time, results

        # Run both approaches
        async_time, async_results = asyncio.run(async_processing())
        thread_time, thread_results = thread_processing()

        # Analyze results
        async_successful = sum(1 for result in async_results if not isinstance(result, Exception) and result is not None)
        thread_successful = sum(1 for result in thread_results if not isinstance(result, Exception) and result is not None)

        # Both approaches should work
        assert async_successful > 0, "Async processing should succeed"
        assert thread_successful > 0, "Thread processing should succeed"

        # For I/O bound operations like API calls, asyncio should be more efficient
        # but we'll just verify both complete successfully

        return {
            "async_time": async_time,
            "thread_time": thread_time,
            "async_successful": async_successful,
            "thread_successful": thread_successful
        }

    @pytest.mark.asyncio
    async def test_scalability_with_increasing_load(self, video_retriever):
        """Test system scalability with increasing number of videos."""
        # Test with increasing batch sizes
        batch_sizes = [1, 2, 3]
        test_url = "https://www.youtube.com/watch?v=Nr7vbOSzpSk"

        scalability_results = {}

        for batch_size in batch_sizes:
            start_time = time.time()

            # Create batch of identical URLs for testing
            batch_urls = [test_url] * batch_size
            tasks = [video_retriever.process_url(url) for url in batch_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            processing_time = end_time - start_time

            successful_processes = sum(1 for result in results if not isinstance(result, Exception) and result is not None)

            scalability_results[batch_size] = {
                "processing_time": processing_time,
                "successful_processes": successful_processes,
                "time_per_video": processing_time / batch_size if batch_size > 0 else 0
            }

            # Verify batch processing
            assert successful_processes > 0, f"At least one video should process in batch of {batch_size}"

        # Verify scalability characteristics
        for batch_size in batch_sizes[1:]:  # Skip first batch for comparison
            prev_batch = batch_sizes[batch_sizes.index(batch_size) - 1]
            current_result = scalability_results[batch_size]
            prev_result = scalability_results[prev_batch]

            # Time per video shouldn't increase dramatically with batch size
            time_ratio = current_result["time_per_video"] / prev_result["time_per_video"]
            assert time_ratio < 3.0, f"Time per video increased too much: {time_ratio}x"

        return scalability_results

    @pytest.mark.asyncio
    async def test_resource_cleanup_efficiency(self, video_retriever, test_videos):
        """Test efficient cleanup of resources during processing."""
        import gc

        # Monitor object count before and after processing
        initial_objects = len(gc.get_objects())

        # Process videos
        tasks = [video_retriever.process_url(url) for url in test_videos]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Force garbage collection
        gc.collect()

        final_objects = len(gc.get_objects())
        object_increase = final_objects - initial_objects

        successful_processes = sum(1 for result in results if not isinstance(result, Exception) and result is not None)

        # Verify processing worked
        assert successful_processes > 0, "At least one video should process successfully"

        # Object count increase should be reasonable
        # Allow for some object creation but not excessive
        assert object_increase < 10000, f"Too many objects created: {object_increase}"

        return {
            "initial_objects": initial_objects,
            "final_objects": final_objects,
            "object_increase": object_increase,
            "videos_processed": successful_processes
        }

    @pytest.mark.asyncio
    async def test_error_handling_performance(self, video_retriever):
        """Test performance impact of error handling."""
        # Mix of valid and invalid URLs
        test_cases = [
            ("valid", "https://www.youtube.com/watch?v=Nr7vbOSzpSk"),
            ("invalid", "https://www.youtube.com/watch?v=definitely_invalid_12345"),
            ("malformed", "not_a_valid_url_at_all"),
            ("valid", "https://www.youtube.com/watch?v=tjFNZlZEJLY"),
        ]

        start_time = time.time()

        results = []
        for test_name, url in test_cases:
            try:
                result = await video_retriever.process_url(url)
                results.append((test_name, result))
            except Exception as e:
                results.append((test_name, str(e)))

        end_time = time.time()
        processing_time = end_time - start_time

        successful_results = sum(1 for name, result in results if result is not None and not isinstance(result, str))

        # Error handling should not significantly impact performance
        assert processing_time < 180, f"Error handling test should complete within 3 minutes, took {processing_time}s"
        assert successful_results > 0, "At least one valid URL should process successfully"

        return {
            "processing_time": processing_time,
            "successful_results": successful_results,
            "total_test_cases": len(test_cases),
            "results": results
        }

    @pytest.mark.asyncio
    async def test_cache_performance_impact(self, test_videos):
        """Test the performance impact of caching."""
        # Test with cache disabled
        retriever_no_cache = VideoIntelligenceRetriever(
            cache_dir="tests/cache",
            use_cache=False,
            use_advanced_extraction=False
        )

        # Test with cache enabled
        retriever_with_cache = VideoIntelligenceRetriever(
            cache_dir="tests/cache",
            use_cache=True,
            use_advanced_extraction=False
        )

        # First run with cache disabled
        start_time = time.time()
        tasks = [retriever_no_cache.process_url(url) for url in test_videos]
        results_no_cache = await asyncio.gather(*tasks, return_exceptions=True)
        no_cache_time = time.time() - start_time

        # Second run with cache enabled
        start_time = time.time()
        tasks = [retriever_with_cache.process_url(url) for url in test_videos]
        results_with_cache = await asyncio.gather(*tasks, return_exceptions=True)
        with_cache_time = time.time() - start_time

        successful_no_cache = sum(1 for result in results_no_cache if not isinstance(result, Exception) and result is not None)
        successful_with_cache = sum(1 for result in results_with_cache if not isinstance(result, Exception) and result is not None)

        # Both should work
        assert successful_no_cache > 0, "No-cache processing should succeed"
        assert successful_with_cache > 0, "Cached processing should succeed"

        # Cache should provide some performance benefit for repeated requests
        # (though this might not be significant for different videos)
        cache_speedup = no_cache_time / max(with_cache_time, 0.1)
        assert cache_speedup > 0.5, f"Cache should not significantly slow down processing, speedup: {cache_speedup}x"

        return {
            "no_cache_time": no_cache_time,
            "with_cache_time": with_cache_time,
            "cache_speedup": cache_speedup,
            "successful_no_cache": successful_no_cache,
            "successful_with_cache": successful_with_cache
        }

    @pytest.mark.asyncio
    async def test_processing_pipeline_efficiency(self, video_retriever, test_videos):
        """Test efficiency of the processing pipeline components."""
        from clipscribe.retrievers.video_processor import VideoProcessor

        processor = VideoProcessor(
            use_advanced_extraction=True,
            use_cache=False
        )

        # Track component-level timing
        component_times = {}

        async def timed_process(url):
            """Process with timing for each component."""
            start_time = time.time()

            # This would ideally track individual component times
            # For now, we track overall processing time
            result = await processor.process_url(url)

            end_time = time.time()
            processing_time = end_time - start_time

            return {
                "url": url,
                "result": result,
                "processing_time": processing_time
            }

        # Process videos and track timing
        tasks = [timed_process(url) for url in test_videos]
        timing_results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_processes = sum(1 for result in timing_results if not isinstance(result, Exception) and result.get("result") is not None)

        # Calculate efficiency metrics
        total_time = sum(result["processing_time"] for result in timing_results if not isinstance(result, Exception))
        avg_time_per_video = total_time / max(successful_processes, 1)

        # Verify reasonable processing times
        assert successful_processes > 0, "At least one video should process successfully"
        assert avg_time_per_video < 120, f"Average processing time should be reasonable, got {avg_time_per_video}s"
        assert total_time < 300, f"Total processing should complete within 5 minutes, took {total_time}s"

        return {
            "total_time": total_time,
            "avg_time_per_video": avg_time_per_video,
            "successful_processes": successful_processes,
            "timing_results": timing_results
        }
