#!/usr/bin/env python3
"""Test Timeline Intelligence v2.0 Integration"""

import asyncio
import logging
import sys
from pathlib import Path
import json
from datetime import datetime
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from src.clipscribe.extractors.multi_video_processor import MultiVideoProcessor
from src.clipscribe.models import VideoCollectionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test videos - using PBS NewsHour for better temporal intelligence testing
TEST_VIDEOS = [
    "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # PBS on AI regulation
    "https://www.youtube.com/watch?v=xYMWTXIkANM"   # PBS on Pegasus spyware
]


async def test_single_video_timeline_v2():
    """Test Timeline v2.0 integration for single video processing."""
    logger.info("=" * 60)
    logger.info("Testing Timeline v2.0 for SINGLE VIDEO processing")
    logger.info("=" * 60)
    
    try:
        # Initialize retriever with cache disabled for testing
        temp_dir = tempfile.mkdtemp()
        retriever = VideoIntelligenceRetriever(
            use_advanced_extraction=True,
            cache_dir=temp_dir  # Use temp dir to avoid cache
        )
        
        # Process single video
        video_url = TEST_VIDEOS[0]
        logger.info(f"Processing video: {video_url}")
        
        start_time = datetime.now()
        video_intelligence = await retriever.process_url(video_url)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        logger.info(f"✅ Processing completed in {processing_time:.2f} seconds")
        
        # Check if Timeline v2.0 data exists
        if hasattr(video_intelligence, 'timeline_v2') and video_intelligence.timeline_v2:
            timeline_data = video_intelligence.timeline_v2
            
            logger.info("\n📊 Timeline v2.0 Results:")
            logger.info(f"- Status: {timeline_data.get('status', 'Unknown')}")
            logger.info(f"- Temporal Events: {timeline_data.get('temporal_events_count', 0)}")
            logger.info(f"- Filtered Events: {timeline_data.get('filtered_events_count', 0)}")
            logger.info(f"- Chapters: {timeline_data.get('chapters_count', 0)}")
            
            if 'quality_metrics' in timeline_data:
                metrics = timeline_data['quality_metrics']
                logger.info(f"- Quality Score: {metrics.get('quality_score', 0):.2f}")
                logger.info(f"- Quality Improvement: {metrics.get('quality_improvement_ratio', 0):.2%}")
            
            if timeline_data.get('status') == 'error':
                logger.error(f"Timeline v2.0 ERROR: {timeline_data.get('error')}")
                logger.info(f"Fallback used: {timeline_data.get('fallback_used', False)}")
            else:
                logger.info("✅ Timeline v2.0 processing successful!")
                
        else:
            logger.warning("⚠️ No Timeline v2.0 data found in video intelligence")
            
    except Exception as e:
        logger.error(f"Single video test failed: {e}", exc_info=True)
        

async def test_multi_video_timeline_v2():
    """Test Timeline v2.0 integration for multi-video collection processing."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Timeline v2.0 for MULTI-VIDEO collection")
    logger.info("=" * 60)
    
    try:
        # Process videos individually first
        temp_dir = tempfile.mkdtemp()
        retriever = VideoIntelligenceRetriever(
            use_advanced_extraction=True,
            cache_dir=temp_dir  # Use temp dir to avoid cache
        )
        videos = []
        
        for url in TEST_VIDEOS:
            logger.info(f"Processing individual video: {url}")
            video = await retriever.process_url(url)
            videos.append(video)
            
        # Process as collection
        processor = MultiVideoProcessor(use_ai_validation=True)
        
        logger.info("\n🔄 Processing collection with Timeline v2.0...")
        start_time = datetime.now()
        
        collection_result = await processor.process_video_collection(
            videos=videos,
            collection_type=VideoCollectionType.CUSTOM_COLLECTION,
            collection_title="Timeline v2.0 Test Collection"
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Collection processing completed in {processing_time:.2f} seconds")
        
        # Check timeline results
        if collection_result and hasattr(collection_result, 'consolidated_timeline'):
            timeline = collection_result.consolidated_timeline
            
            logger.info("\n📊 Timeline v2.0 Collection Results:")
            logger.info(f"- Timeline ID: {timeline.timeline_id}")
            logger.info(f"- Total Events: {len(timeline.events)}")
            logger.info(f"- Summary: {timeline.summary[:100]}...")
            
            # Check for fallback
            if "fallback" in timeline.timeline_id.lower() or "fallback" in timeline.summary.lower():
                logger.warning("⚠️ Timeline v2.0 fell back to basic timeline")
                # Extract reason from summary if available
                if "Reason:" in timeline.summary:
                    reason = timeline.summary.split("Reason:")[1].strip()
                    logger.error(f"Fallback reason: {reason}")
            else:
                logger.info("✅ Timeline v2.0 processing successful!")
                
            # Show first few events
            logger.info("\n📅 First 5 Timeline Events:")
            for i, event in enumerate(timeline.events[:5]):
                logger.info(f"{i+1}. [{event.timestamp}] {event.description[:80]}...")
                logger.info(f"   Source: {event.source_video_title}")
                logger.info(f"   Date Source: {event.date_source}")
                
        else:
            logger.warning("⚠️ No consolidated timeline found in collection result")
            
    except Exception as e:
        logger.error(f"Multi-video test failed: {e}", exc_info=True)


async def main():
    """Run all Timeline v2.0 tests."""
    logger.info("🚀 Starting Timeline Intelligence v2.0 Integration Tests")
    logger.info(f"Test Time: {datetime.now()}")
    
    # Test single video
    await test_single_video_timeline_v2()
    
    # Test multi-video collection
    await test_multi_video_timeline_v2()
    
    logger.info("\n✅ All tests completed!")
    

if __name__ == "__main__":
    asyncio.run(main()) 