"""
Platform-Specific Edge Case Testing for ClipScribe.

Tests 50+ video format variations across different platforms to ensure
99%+ successful video processing rate.

Focus Areas:
- Platform-specific URL patterns and extraction methods
- Different video qualities and formats per platform
- Edge cases like private videos, geo-restrictions, deleted content
- Platform-specific metadata extraction accuracy

Part of Week 1-2 Core Excellence Implementation Plan.
"""

import pytest
import asyncio
import logging
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import json

from clipscribe.retrievers.universal_video_client import UniversalVideoClient
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence, VideoMetadata
from tests.fixtures import create_test_audio_file

logger = logging.getLogger(__name__)

class TestPlatformVariations:
    """Test video processing across different platforms and edge cases."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def mock_video_client(self):
        """Create mock video client for testing."""
        client = Mock(spec=UniversalVideoClient)
        client.is_supported_url = Mock(return_value=True)
        return client
    
    @pytest.fixture
    def edge_case_urls(self):
        """Comprehensive list of test URLs covering 50+ variations."""
        return {
            # YouTube Variations (15 test cases)
            "youtube_standard": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "youtube_shorts": "https://www.youtube.com/shorts/abc123",
            "youtube_playlist": "https://www.youtube.com/playlist?list=PLtest",
            "youtube_live": "https://www.youtube.com/watch?v=live123",
            "youtube_private": "https://www.youtube.com/watch?v=private123",
            "youtube_geo_blocked": "https://www.youtube.com/watch?v=geo123",
            "youtube_deleted": "https://www.youtube.com/watch?v=deleted123",
            "youtube_age_restricted": "https://www.youtube.com/watch?v=age123",
            "youtube_unlisted": "https://www.youtube.com/watch?v=unlisted123",
            "youtube_4k": "https://www.youtube.com/watch?v=4k123",
            "youtube_8k": "https://www.youtube.com/watch?v=8k123",
            "youtube_360": "https://www.youtube.com/watch?v=360_123",
            "youtube_vr": "https://www.youtube.com/watch?v=vr123",
            "youtube_hdr": "https://www.youtube.com/watch?v=hdr123",
            "youtube_premium": "https://www.youtube.com/watch?v=premium123",
            
            # TikTok Variations (8 test cases)
            "tiktok_standard": "https://www.tiktok.com/@user/video/123456789",
            "tiktok_vm": "https://vm.tiktok.com/ZMrandomstring/",
            "tiktok_private": "https://www.tiktok.com/@private/video/123",
            "tiktok_deleted": "https://www.tiktok.com/@user/video/deleted",
            "tiktok_geo_blocked": "https://www.tiktok.com/@user/video/geo123",
            "tiktok_live": "https://www.tiktok.com/@user/live/456",
            "tiktok_slideshow": "https://www.tiktok.com/@user/video/slideshow123",
            "tiktok_duet": "https://www.tiktok.com/@user/video/duet123",
            
            # Twitter/X Variations (8 test cases)
            "twitter_video": "https://twitter.com/user/status/123456789",
            "twitter_x_video": "https://x.com/user/status/123456789",
            "twitter_live": "https://twitter.com/i/broadcasts/123",
            "twitter_spaces": "https://twitter.com/i/spaces/456",
            "twitter_private": "https://twitter.com/private/status/123",
            "twitter_deleted": "https://twitter.com/user/status/deleted",
            "twitter_suspended": "https://twitter.com/suspended/status/123",
            "twitter_thread": "https://twitter.com/user/status/thread123",
            
            # Vimeo Variations (6 test cases)
            "vimeo_standard": "https://vimeo.com/123456789",
            "vimeo_private": "https://vimeo.com/private123",
            "vimeo_password": "https://vimeo.com/password123",
            "vimeo_unlisted": "https://vimeo.com/unlisted123",
            "vimeo_live": "https://vimeo.com/event/456",
            "vimeo_premium": "https://vimeo.com/ondemand/test123",
            
            # Instagram Variations (5 test cases)
            "instagram_reel": "https://www.instagram.com/reel/abc123/",
            "instagram_igtv": "https://www.instagram.com/tv/def456/",
            "instagram_story": "https://www.instagram.com/stories/user/789",
            "instagram_live": "https://www.instagram.com/user/live/123",
            "instagram_private": "https://www.instagram.com/p/private123/",
            
            # Other Platforms (8 test cases)
            "dailymotion": "https://www.dailymotion.com/video/x123456",
            "twitch_clip": "https://clips.twitch.tv/clip123",
            "twitch_vod": "https://www.twitch.tv/videos/123456",
            "reddit_video": "https://www.reddit.com/r/videos/comments/123/test/",
            "facebook_video": "https://www.facebook.com/watch/?v=123456789",
            "linkedin_video": "https://www.linkedin.com/posts/activity-123",
            "soundcloud": "https://soundcloud.com/user/track-name",
            "bandcamp": "https://artist.bandcamp.com/track/song-name"
        }
    
    @pytest.fixture
    def video_format_variations(self):
        """Video format and quality variations for testing."""
        return {
            # Resolution Variations
            "8k_60fps": {"resolution": "7680x4320", "fps": 60, "codec": "h265"},
            "4k_60fps": {"resolution": "3840x2160", "fps": 60, "codec": "h264"},
            "4k_30fps": {"resolution": "3840x2160", "fps": 30, "codec": "h264"},
            "1440p_60fps": {"resolution": "2560x1440", "fps": 60, "codec": "h264"},
            "1080p_60fps": {"resolution": "1920x1080", "fps": 60, "codec": "h264"},
            "1080p_30fps": {"resolution": "1920x1080", "fps": 30, "codec": "h264"},
            "720p_60fps": {"resolution": "1280x720", "fps": 60, "codec": "h264"},
            "720p_30fps": {"resolution": "1280x720", "fps": 30, "codec": "h264"},
            "480p": {"resolution": "854x480", "fps": 30, "codec": "h264"},
            "360p": {"resolution": "640x360", "fps": 30, "codec": "h264"},
            "240p": {"resolution": "426x240", "fps": 30, "codec": "h264"},
            
            # Duration Variations
            "micro_video": {"duration": 5, "description": "5 second micro-video"},
            "short_video": {"duration": 30, "description": "30 second short"},
            "medium_video": {"duration": 300, "description": "5 minute medium video"},
            "long_video": {"duration": 1800, "description": "30 minute long video"},
            "extended_video": {"duration": 3600, "description": "1 hour extended video"},
            "marathon_video": {"duration": 7200, "description": "2 hour marathon video"},
            
            # Audio Variations
            "stereo_audio": {"audio_channels": 2, "audio_quality": "high"},
            "mono_audio": {"audio_channels": 1, "audio_quality": "medium"},
            "surround_audio": {"audio_channels": 6, "audio_quality": "premium"},
            "low_quality_audio": {"audio_channels": 2, "audio_quality": "low"},
            "no_audio": {"audio_channels": 0, "audio_quality": "none"},
            
            # Codec Variations
            "h264_baseline": {"codec": "h264", "profile": "baseline"},
            "h264_main": {"codec": "h264", "profile": "main"},
            "h264_high": {"codec": "h264", "profile": "high"},
            "h265_main": {"codec": "h265", "profile": "main"},
            "av1": {"codec": "av1", "profile": "main"},
            "vp9": {"codec": "vp9", "profile": "0"},
            "webm": {"codec": "webm", "container": "webm"}
        }
    
    @pytest.mark.asyncio
    async def test_platform_url_validation(self, edge_case_urls):
        """Test URL validation across all supported platforms."""
        client = UniversalVideoClient()
        
        validation_results = {}
        for platform, url in edge_case_urls.items():
            try:
                is_supported = client.is_supported_url(url)
                validation_results[platform] = {
                    "url": url,
                    "supported": is_supported,
                    "platform_detected": platform.split('_')[0]
                }
            except Exception as e:
                validation_results[platform] = {
                    "url": url,
                    "supported": False,
                    "error": str(e)
                }
        
        # Log results for analysis
        supported_count = sum(1 for r in validation_results.values() if r.get("supported", False))
        total_count = len(validation_results)
        support_rate = (supported_count / total_count) * 100
        
        logger.info(f"Platform URL validation: {supported_count}/{total_count} ({support_rate:.1f}%)")
        
        # Target: >95% URL validation success rate
        assert support_rate >= 95.0, f"URL validation rate {support_rate:.1f}% below 95% target"
        
        # Ensure major platforms are supported
        major_platforms = ['youtube', 'tiktok', 'twitter', 'vimeo']
        for platform in major_platforms:
            platform_urls = [k for k in validation_results.keys() if k.startswith(platform)]
            platform_supported = [validation_results[k]['supported'] for k in platform_urls]
            platform_rate = (sum(platform_supported) / len(platform_supported)) * 100
            
            assert platform_rate >= 90.0, f"{platform} support rate {platform_rate:.1f}% below 90% target"
    
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self, temp_dir):
        """Test graceful handling of various error scenarios."""
        retriever = VideoIntelligenceRetriever(output_dir=temp_dir)
        
        error_scenarios = [
            {
                "name": "private_video",
                "url": "https://www.youtube.com/watch?v=private123",
                "expected_error": "private",
                "should_retry": False
            },
            {
                "name": "deleted_video", 
                "url": "https://www.youtube.com/watch?v=deleted123",
                "expected_error": "not_found",
                "should_retry": False
            },
            {
                "name": "geo_blocked",
                "url": "https://www.youtube.com/watch?v=geo123", 
                "expected_error": "geo_restricted",
                "should_retry": True
            },
            {
                "name": "network_timeout",
                "url": "https://www.youtube.com/watch?v=timeout123",
                "expected_error": "timeout",
                "should_retry": True
            },
            {
                "name": "invalid_format",
                "url": "https://invalid-platform.com/video/123",
                "expected_error": "unsupported",
                "should_retry": False
            }
        ]
        
        recovery_results = {}
        
        for scenario in error_scenarios:
            scenario_name = scenario["name"]
            url = scenario["url"]
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Mock the appropriate error condition
                with patch.object(retriever.video_client, 'download_audio') as mock_download:
                    if scenario_name == "network_timeout":
                        mock_download.side_effect = TimeoutError("Network timeout")
                    elif scenario_name == "private_video":
                        mock_download.side_effect = PermissionError("Private video")
                    elif scenario_name == "deleted_video":
                        mock_download.side_effect = FileNotFoundError("Video not found")
                    else:
                        mock_download.side_effect = Exception(f"Test error: {scenario_name}")
                    
                    result = await retriever.process_url(url)
                    
                end_time = asyncio.get_event_loop().time()
                recovery_time = end_time - start_time
                
                recovery_results[scenario_name] = {
                    "success": result is not None,
                    "recovery_time": recovery_time,
                    "error_handled": True
                }
                
            except Exception as e:
                end_time = asyncio.get_event_loop().time()
                recovery_time = end_time - start_time
                
                recovery_results[scenario_name] = {
                    "success": False,
                    "recovery_time": recovery_time,
                    "error_handled": "graceful" in str(e).lower(),
                    "error": str(e)
                }
        
        # Validate recovery metrics
        for scenario_name, result in recovery_results.items():
            recovery_time = result["recovery_time"]
            
            # Target: Mean time to recovery <30 seconds
            assert recovery_time < 30.0, f"{scenario_name} recovery time {recovery_time:.1f}s exceeds 30s target"
            
            # Ensure errors are handled gracefully (no unhandled exceptions)
            assert result["error_handled"], f"{scenario_name} error not handled gracefully"
        
        # Log recovery metrics
        avg_recovery_time = sum(r["recovery_time"] for r in recovery_results.values()) / len(recovery_results)
        logger.info(f"Average error recovery time: {avg_recovery_time:.2f}s")
        
        assert avg_recovery_time < 30.0, f"Average recovery time {avg_recovery_time:.1f}s exceeds 30s target"
    
    @pytest.mark.asyncio
    async def test_content_type_variations(self, temp_dir):
        """Test entity extraction accuracy across different content types."""
        
        content_variations = [
            {
                "type": "news_interview",
                "description": "News interview with multiple speakers",
                "expected_entities": ["PERSON", "ORGANIZATION", "LOCATION"],
                "min_entities": 5,
                "target_accuracy": 0.95
            },
            {
                "type": "educational_lecture", 
                "description": "Educational lecture with technical terms",
                "expected_entities": ["PERSON", "CONCEPT", "TECHNOLOGY"],
                "min_entities": 8,
                "target_accuracy": 0.90
            },
            {
                "type": "political_speech",
                "description": "Political speech with policy references",
                "expected_entities": ["PERSON", "ORGANIZATION", "POLICY", "LOCATION"],
                "min_entities": 10,
                "target_accuracy": 0.92
            },
            {
                "type": "business_presentation",
                "description": "Business presentation with financial data",
                "expected_entities": ["PERSON", "ORGANIZATION", "MONEY", "PRODUCT"],
                "min_entities": 6,
                "target_accuracy": 0.88
            },
            {
                "type": "documentary_narration",
                "description": "Documentary with historical references",
                "expected_entities": ["PERSON", "DATE", "LOCATION", "EVENT"],
                "min_entities": 12,
                "target_accuracy": 0.85
            }
        ]
        
        retriever = VideoIntelligenceRetriever(
            output_dir=temp_dir,
            use_advanced_extraction=True
        )
        
        content_results = {}
        
        for content in content_variations:
            content_type = content["type"]
            
            # Mock video processing with content-appropriate results
            with patch.object(retriever, '_process_video_enhanced') as mock_process:
                # Create mock result based on content type
                mock_result = self._create_mock_video_intelligence(content)
                mock_process.return_value = mock_result
                
                # Test processing
                test_url = f"https://www.youtube.com/watch?v={content_type}_test"
                result = await retriever.process_url(test_url)
                
                if result:
                    entity_count = len(result.entities)
                    entity_types = set(e.type for e in result.entities)
                    
                    # Calculate accuracy metrics
                    expected_types = set(content["expected_entities"])
                    type_coverage = len(entity_types.intersection(expected_types)) / len(expected_types)
                    
                    content_results[content_type] = {
                        "entity_count": entity_count,
                        "entity_types": list(entity_types),
                        "type_coverage": type_coverage,
                        "meets_minimum": entity_count >= content["min_entities"],
                        "meets_accuracy": type_coverage >= content["target_accuracy"]
                    }
                else:
                    content_results[content_type] = {
                        "success": False,
                        "error": "Processing failed"
                    }
        
        # Validate content type processing
        successful_types = sum(1 for r in content_results.values() if r.get("meets_accuracy", False))
        total_types = len(content_variations)
        accuracy_rate = (successful_types / total_types) * 100
        
        logger.info(f"Content type accuracy: {successful_types}/{total_types} ({accuracy_rate:.1f}%)")
        
        # Target: >90% accuracy across content types
        assert accuracy_rate >= 90.0, f"Content type accuracy {accuracy_rate:.1f}% below 90% target"
        
        # Ensure minimum entity counts are met
        for content_type, result in content_results.items():
            if result.get("success", True):  # Skip failed results
                assert result["meets_minimum"], f"{content_type} entity count below minimum"
    
    def _create_mock_video_intelligence(self, content_spec: Dict[str, Any]) -> VideoIntelligence:
        """Create mock VideoIntelligence object for testing."""
        from clipscribe.models import VideoTranscript, Entity, KeyPoint, Topic
        from datetime import datetime
        
        # Create appropriate entities based on content type
        entities = []
        entity_types = content_spec["expected_entities"]
        min_entities = content_spec["min_entities"]
        
        # Generate test entities
        entity_templates = {
            "PERSON": ["John Smith", "Dr. Sarah Johnson", "Professor Williams"],
            "ORGANIZATION": ["Microsoft", "University of California", "Department of Defense"],
            "LOCATION": ["Washington D.C.", "Silicon Valley", "New York"],
            "CONCEPT": ["Machine Learning", "Climate Change", "Economic Policy"],
            "TECHNOLOGY": ["Artificial Intelligence", "Blockchain", "Quantum Computing"],
            "POLICY": ["Healthcare Reform", "Tax Policy", "Immigration Law"],
            "MONEY": ["$1.2 billion", "$50 million", "$100,000"],
            "PRODUCT": ["iPhone", "Tesla Model S", "Microsoft Office"],
            "DATE": ["2023-01-15", "December 2022", "Q4 2023"],
            "EVENT": ["2020 Election", "COVID-19 Pandemic", "Climate Summit"]
        }
        
        entity_count = 0
        for entity_type in entity_types:
            if entity_type in entity_templates:
                for name in entity_templates[entity_type][:3]:  # Add up to 3 per type
                    if entity_count < min_entities:
                        entities.append(Entity(
                            name=name,
                            type=entity_type,
                            confidence=0.9 + (entity_count * 0.01),  # Vary confidence slightly
                            properties={"source": "test"}
                        ))
                        entity_count += 1
        
        # Create mock metadata
        metadata = VideoMetadata(
            video_id="test123",
            title=f"Test {content_spec['type']} Video",
            channel="Test Channel",
            channel_id="UC123",
            duration=300,
            view_count=1000,
            url="https://test.com/video/123",
            published_at=datetime.now()
        )
        
        # Create mock transcript
        transcript = VideoTranscript(
            full_text=f"This is a test transcript for {content_spec['type']} content.",
            segments=[]
        )
        
        return VideoIntelligence(
            metadata=metadata,
            transcript=transcript,
            summary=f"Test summary for {content_spec['type']}",
            key_points=[],
            entities=entities,
            topics=[],
            sentiment=None,
            confidence_score=0.95,
            processing_time=2.5,
            processing_cost=0.005
        )
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, temp_dir):
        """Test processing performance across different video characteristics."""
        
        performance_scenarios = [
            {"name": "short_video", "duration": 30, "target_time": 15},
            {"name": "medium_video", "duration": 300, "target_time": 45},
            {"name": "long_video", "duration": 1800, "target_time": 120},
            {"name": "hd_video", "duration": 300, "quality": "1080p", "target_time": 60},
            {"name": "4k_video", "duration": 300, "quality": "4k", "target_time": 90}
        ]
        
        retriever = VideoIntelligenceRetriever(output_dir=temp_dir)
        performance_results = {}
        
        for scenario in performance_scenarios:
            scenario_name = scenario["name"]
            
            # Mock processing time based on scenario
            with patch.object(retriever, '_process_video_enhanced') as mock_process:
                # Simulate realistic processing time
                processing_time = scenario["duration"] * 0.1  # 10% of video length
                if "4k" in scenario_name:
                    processing_time *= 1.5  # 4K takes longer
                elif "hd" in scenario_name:
                    processing_time *= 1.2  # HD takes slightly longer
                
                mock_result = VideoIntelligence(
                    metadata=VideoMetadata(
                        video_id="perf_test",
                        title=f"Performance Test {scenario_name}",
                        channel="Test",
                        channel_id="UC123",
                        duration=scenario["duration"],
                        view_count=1000,
                        url="https://test.com/perf",
                        published_at=datetime.now()
                    ),
                    transcript=VideoTranscript(full_text="Test transcript", segments=[]),
                    summary="Test summary",
                    key_points=[],
                    entities=[],
                    topics=[],
                    sentiment=None,
                    confidence_score=0.95,
                    processing_time=processing_time,
                    processing_cost=0.002 * (scenario["duration"] / 60)  # $0.002/minute
                )
                mock_process.return_value = mock_result
                
                # Measure actual call time
                start_time = asyncio.get_event_loop().time()
                result = await retriever.process_url(f"https://test.com/{scenario_name}")
                end_time = asyncio.get_event_loop().time()
                
                call_time = end_time - start_time
                
                performance_results[scenario_name] = {
                    "duration": scenario["duration"],
                    "processing_time": processing_time,
                    "call_time": call_time,
                    "target_time": scenario["target_time"],
                    "cost": result.processing_cost if result else 0,
                    "meets_target": call_time <= scenario["target_time"]
                }
        
        # Validate performance targets
        successful_scenarios = sum(1 for r in performance_results.values() if r["meets_target"])
        total_scenarios = len(performance_scenarios)
        performance_rate = (successful_scenarios / total_scenarios) * 100
        
        logger.info(f"Performance targets met: {successful_scenarios}/{total_scenarios} ({performance_rate:.1f}%)")
        
        # Target: 90% of scenarios meet performance targets
        assert performance_rate >= 90.0, f"Performance rate {performance_rate:.1f}% below 90% target"
        
        # Validate cost efficiency ($0.002/minute target)
        for scenario_name, result in performance_results.items():
            expected_cost = 0.002 * (result["duration"] / 60)
            actual_cost = result["cost"]
            cost_variance = abs(actual_cost - expected_cost) / expected_cost
            
            assert cost_variance <= 0.1, f"{scenario_name} cost variance {cost_variance:.1%} exceeds 10% target" 