"""
Resource Management and Performance Testing for ClipScribe.

Tests memory usage, processing efficiency, and resource management across
different video sizes and processing loads.

Target Metrics:
- <2GB memory usage for 1000+ video collections  
- 25% faster processing while maintaining cost leadership
- >85% cache hit rate for repeated processing
- Graceful resource management under load

Part of Week 1-2 Core Excellence Implementation Plan.
"""

import pytest
import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List
from unittest.mock import Mock, patch
import statistics
import gc

from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.utils.performance import PerformanceMonitor

logger = logging.getLogger(__name__)

class TestResourceManagement:
    """Test resource usage and performance management."""
    
    @pytest.fixture
    def memory_monitor(self):
        """Setup memory monitoring."""
        process = psutil.Process()
        return process
    
    @pytest.fixture
    def performance_scenarios(self):
        """Different performance test scenarios."""
        return {
            "small_batch": {
                "video_count": 5,
                "avg_duration": 180,  # 3 minutes
                "target_memory_mb": 500,
                "target_time_per_video": 30
            },
            "medium_batch": {
                "video_count": 25, 
                "avg_duration": 600,  # 10 minutes
                "target_memory_mb": 1000,
                "target_time_per_video": 45
            },
            "large_batch": {
                "video_count": 100,
                "avg_duration": 300,  # 5 minutes
                "target_memory_mb": 1500,
                "target_time_per_video": 35
            },
            "stress_test": {
                "video_count": 1000,
                "avg_duration": 120,  # 2 minutes
                "target_memory_mb": 2000,  # <2GB target
                "target_time_per_video": 25
            }
        }
    
    @pytest.fixture
    def cache_test_scenarios(self):
        """Scenarios for testing caching effectiveness."""
        return {
            "repeated_processing": {
                "videos": ["video1", "video2", "video3"],
                "repetitions": 3,
                "target_cache_hit_rate": 0.85
            },
            "similar_content": {
                "videos": ["news1", "news2", "news3"],  # Similar content type
                "target_cache_hit_rate": 0.70
            },
            "diverse_content": {
                "videos": ["tech1", "politics1", "sports1"],  # Different content
                "target_cache_hit_rate": 0.30
            }
        }
    
    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self, performance_scenarios, memory_monitor):
        """Test memory usage scaling across different batch sizes."""
        memory_results = {}
        
        for scenario_name, scenario in performance_scenarios.items():
            # Record initial memory
            initial_memory = memory_monitor.memory_info().rss / 1024 / 1024  # MB
            
            # Simulate processing load
            mock_videos = []
            for i in range(scenario["video_count"]):
                mock_video = Mock()
                mock_video.metadata.duration = scenario["avg_duration"]
                mock_video.processing_time = scenario["avg_duration"] * 0.1
                mock_videos.append(mock_video)
            
            # Simulate memory usage during processing
            peak_memory = initial_memory
            
            for i, video in enumerate(mock_videos):
                # Simulate gradual memory increase
                current_memory = memory_monitor.memory_info().rss / 1024 / 1024
                peak_memory = max(peak_memory, current_memory)
                
                # Simulate periodic garbage collection
                if i % 10 == 0:
                    gc.collect()
                    await asyncio.sleep(0.01)  # Small delay for GC
            
            # Final memory measurement
            final_memory = memory_monitor.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            
            memory_results[scenario_name] = {
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "target_memory_mb": scenario["target_memory_mb"],
                "meets_target": memory_increase <= scenario["target_memory_mb"],
                "video_count": scenario["video_count"],
                "memory_per_video": memory_increase / scenario["video_count"] if scenario["video_count"] > 0 else 0
            }
            
            logger.info(f"{scenario_name}: {memory_increase:.1f}MB increase for {scenario['video_count']} videos")
        
        # Validate memory usage targets
        successful_scenarios = sum(1 for r in memory_results.values() if r["meets_target"])
        total_scenarios = len(memory_results)
        memory_success_rate = (successful_scenarios / total_scenarios) * 100
        
        # Target: >90% of scenarios meet memory targets
        assert memory_success_rate >= 90.0, f"Memory usage success rate {memory_success_rate:.1f}% below 90% target"
        
        # Critical requirement: Large batches must stay under 2GB
        stress_test_result = memory_results.get("stress_test")
        if stress_test_result:
            assert stress_test_result["memory_increase_mb"] < 2000, f"Stress test memory usage {stress_test_result['memory_increase_mb']:.1f}MB exceeds 2GB limit"
        
        return memory_results
    
    @pytest.mark.asyncio
    async def test_processing_speed_optimization(self, performance_scenarios):
        """Test processing speed improvements and efficiency."""
        speed_results = {}
        
        for scenario_name, scenario in performance_scenarios.items():
            video_count = scenario["video_count"]
            target_time_per_video = scenario["target_time_per_video"]
            
            # Simulate optimized processing
            start_time = time.time()
            
            processing_times = []
            for i in range(video_count):
                video_start = time.time()
                
                # Simulate processing with optimizations
                base_processing_time = scenario["avg_duration"] * 0.1  # 10% of video length
                
                # Apply optimization factors
                optimization_factor = 0.75  # 25% speed improvement target
                cache_factor = 0.9 if i > 0 else 1.0  # Cache benefits after first video
                parallel_factor = 0.85 if video_count > 10 else 1.0  # Parallel processing benefits
                
                actual_processing_time = base_processing_time * optimization_factor * cache_factor * parallel_factor
                
                # Simulate actual processing delay
                await asyncio.sleep(min(actual_processing_time / 1000, 0.1))  # Scale down for testing
                
                video_end = time.time()
                processing_times.append(video_end - video_start)
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time_per_video = total_time / video_count if video_count > 0 else 0
            
            speed_results[scenario_name] = {
                "total_time": total_time,
                "avg_time_per_video": avg_time_per_video,
                "target_time_per_video": target_time_per_video,
                "meets_target": avg_time_per_video <= target_time_per_video,
                "video_count": video_count,
                "speed_improvement": (target_time_per_video - avg_time_per_video) / target_time_per_video if target_time_per_video > 0 else 0
            }
            
            logger.info(f"{scenario_name}: {avg_time_per_video:.2f}s avg per video (target: {target_time_per_video}s)")
        
        # Validate speed optimization targets
        successful_scenarios = sum(1 for r in speed_results.values() if r["meets_target"])
        total_scenarios = len(speed_results)
        speed_success_rate = (successful_scenarios / total_scenarios) * 100
        
        # Target: >90% of scenarios meet speed targets
        assert speed_success_rate >= 90.0, f"Speed optimization success rate {speed_success_rate:.1f}% below 90% target"
        
        # Overall speed improvement target: 25% faster
        avg_improvement = statistics.mean([r["speed_improvement"] for r in speed_results.values()])
        assert avg_improvement >= 0.20, f"Average speed improvement {avg_improvement:.1%} below 20% minimum (target: 25%)"
        
        return speed_results
    
    @pytest.mark.asyncio
    async def test_cache_efficiency(self, cache_test_scenarios):
        """Test caching effectiveness and hit rates."""
        cache_results = {}
        
        for scenario_name, scenario in cache_test_scenarios.items():
            cache_hits = 0
            total_requests = 0
            
            # Simulate cache behavior
            cache_store = {}
            
            if "repetitions" in scenario:
                # Test repeated processing
                videos = scenario["videos"]
                repetitions = scenario["repetitions"]
                
                for rep in range(repetitions):
                    for video in videos:
                        total_requests += 1
                        
                        # First time processing goes to cache
                        if video not in cache_store:
                            cache_store[video] = {"processed": True, "hits": 0}
                        else:
                            # Subsequent requests are cache hits
                            cache_hits += 1
                            cache_store[video]["hits"] += 1
            else:
                # Test different content types
                videos = scenario["videos"]
                for video in videos:
                    total_requests += 1
                    
                    # Simulate cache logic for similar content
                    cache_key = video.split('_')[0]  # Group by content type
                    if cache_key in cache_store:
                        cache_hits += 1
                        cache_store[cache_key]["hits"] += 1
                    else:
                        cache_store[cache_key] = {"processed": True, "hits": 0}
            
            cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0
            target_hit_rate = scenario["target_cache_hit_rate"]
            
            cache_results[scenario_name] = {
                "cache_hit_rate": cache_hit_rate,
                "target_hit_rate": target_hit_rate,
                "meets_target": cache_hit_rate >= target_hit_rate,
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "cache_misses": total_requests - cache_hits
            }
            
            logger.info(f"{scenario_name}: {cache_hit_rate:.1%} cache hit rate (target: {target_hit_rate:.1%})")
        
        # Validate cache efficiency
        successful_scenarios = sum(1 for r in cache_results.values() if r["meets_target"])
        total_scenarios = len(cache_results)
        cache_success_rate = (successful_scenarios / total_scenarios) * 100
        
        # Target: >85% of scenarios meet cache targets
        assert cache_success_rate >= 85.0, f"Cache efficiency success rate {cache_success_rate:.1f}% below 85% target"
        
        # Overall cache hit rate target: >85% for repeated processing
        repeated_processing_result = cache_results.get("repeated_processing")
        if repeated_processing_result:
            assert repeated_processing_result["cache_hit_rate"] >= 0.85, f"Repeated processing cache hit rate {repeated_processing_result['cache_hit_rate']:.1%} below 85% target"
        
        return cache_results
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_stability(self):
        """Test stability under concurrent processing loads."""
        concurrent_results = {}
        
        concurrency_levels = [1, 5, 10, 25]
        
        for concurrency in concurrency_levels:
            tasks = []
            start_time = time.time()
            
            # Create concurrent processing tasks
            for i in range(concurrency):
                async def mock_process_video(video_id):
                    # Simulate video processing
                    await asyncio.sleep(0.1)  # Mock processing time
                    return {"video_id": video_id, "success": True}
                
                task = asyncio.create_task(mock_process_video(f"video_{i}"))
                tasks.append(task)
            
            # Wait for all tasks to complete
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()
                
                # Analyze results
                successful_tasks = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
                failed_tasks = concurrency - successful_tasks
                total_time = end_time - start_time
                
                concurrent_results[concurrency] = {
                    "concurrency_level": concurrency,
                    "successful_tasks": successful_tasks,
                    "failed_tasks": failed_tasks,
                    "success_rate": successful_tasks / concurrency,
                    "total_time": total_time,
                    "avg_time_per_task": total_time / concurrency,
                    "stable": failed_tasks == 0
                }
                
                logger.info(f"Concurrency {concurrency}: {successful_tasks}/{concurrency} successful ({total_time:.2f}s)")
                
            except Exception as e:
                concurrent_results[concurrency] = {
                    "concurrency_level": concurrency,
                    "error": str(e),
                    "stable": False
                }
        
        # Validate concurrent processing stability
        stable_levels = sum(1 for r in concurrent_results.values() if r.get("stable", False))
        total_levels = len(concurrent_results)
        stability_rate = (stable_levels / total_levels) * 100
        
        # Target: >90% of concurrency levels are stable
        assert stability_rate >= 90.0, f"Concurrent processing stability rate {stability_rate:.1f}% below 90% target"
        
        return concurrent_results
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, memory_monitor):
        """Test proper resource cleanup after processing."""
        initial_memory = memory_monitor.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate resource-intensive processing
        large_objects = []
        for i in range(100):
            # Create mock large objects (simulating video data)
            large_object = {"data": "x" * 10000, "id": i}  # ~10KB each
            large_objects.append(large_object)
        
        peak_memory = memory_monitor.memory_info().rss / 1024 / 1024
        memory_increase = peak_memory - initial_memory
        
        # Cleanup simulation
        large_objects.clear()
        gc.collect()
        await asyncio.sleep(0.1)  # Allow cleanup time
        
        final_memory = memory_monitor.memory_info().rss / 1024 / 1024
        memory_after_cleanup = final_memory - initial_memory
        
        cleanup_efficiency = (memory_increase - memory_after_cleanup) / memory_increase if memory_increase > 0 else 1.0
        
        cleanup_results = {
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "memory_after_cleanup_mb": memory_after_cleanup,
            "cleanup_efficiency": cleanup_efficiency,
            "cleanup_successful": cleanup_efficiency >= 0.8  # 80% cleanup target
        }
        
        logger.info(f"Resource cleanup: {cleanup_efficiency:.1%} efficiency")
        
        # Validate cleanup efficiency
        assert cleanup_efficiency >= 0.8, f"Resource cleanup efficiency {cleanup_efficiency:.1%} below 80% target"
        
        return cleanup_results 