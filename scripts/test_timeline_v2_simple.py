#!/usr/bin/env python3
"""Simple test to debug Timeline v2.0 issues"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from src.clipscribe.extractors.multi_video_processor import MultiVideoProcessor
from src.clipscribe.models import VideoCollectionType

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('timeline_v2_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Focus on timeline components
logging.getLogger('src.clipscribe.timeline').setLevel(logging.DEBUG)
logging.getLogger('src.clipscribe.extractors.multi_video_processor').setLevel(logging.DEBUG)


async def test_timeline_v2_debug():
    """Debug Timeline v2.0 with detailed logging"""
    logger.info("=" * 60)
    logger.info("Timeline v2.0 Debug Test")
    logger.info("=" * 60)
    
    # Use videos we know work
    test_urls = [
        "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # PBS on AI regulation
        "https://www.youtube.com/watch?v=xYMWTXIkANM"   # PBS on Pegasus spyware
    ]
    
    try:
        # Process videos
        retriever = VideoIntelligenceRetriever(use_advanced_extraction=True)
        videos = []
        
        for url in test_urls:
            logger.info(f"\n{'='*40}")
            logger.info(f"Processing: {url}")
            video = await retriever.process_url(url)
            
            if video:
                logger.info(f"✅ Video processed successfully")
                logger.info(f"   - Title: {video.metadata.title}")
                logger.info(f"   - Entities: {len(video.entities)}")
                logger.info(f"   - Key Points: {len(video.key_points)}")
                
                # Check if Timeline v2.0 data exists
                if hasattr(video, 'timeline_v2'):
                    logger.info(f"   - Timeline v2.0 data: {bool(video.timeline_v2)}")
                    if video.timeline_v2:
                        logger.info(f"     Status: {video.timeline_v2.get('status')}")
                        logger.info(f"     Events: {video.timeline_v2.get('temporal_events_count', 0)}")
                else:
                    logger.warning("   - No timeline_v2 attribute found")
                    
                # Show sample entities
                if video.entities:
                    logger.info("   - Sample entities:")
                    for entity in video.entities[:5]:
                        logger.info(f"     • {entity.name} ({entity.type}) - confidence: {entity.confidence}")
                        
                videos.append(video)
            else:
                logger.error(f"❌ Failed to process video")
                
        if len(videos) < 2:
            logger.error("Not enough videos for collection processing")
            return
            
        # Process collection
        logger.info(f"\n{'='*60}")
        logger.info("Processing multi-video collection...")
        
        processor = MultiVideoProcessor(use_ai_validation=True)
        collection = await processor.process_video_collection(
            videos=videos,
            collection_type=VideoCollectionType.CUSTOM_COLLECTION,
            collection_title="Timeline v2.0 Debug Collection"
        )
        
        # Check results
        if collection and hasattr(collection, 'consolidated_timeline'):
            timeline = collection.consolidated_timeline
            logger.info(f"\n✅ Collection processed successfully")
            logger.info(f"Timeline ID: {timeline.timeline_id}")
            logger.info(f"Total events: {len(timeline.events)}")
            logger.info(f"Summary: {timeline.summary[:200]}...")
            
            # Check if it's fallback
            if "fallback" in timeline.timeline_id:
                logger.warning("\n⚠️ USING FALLBACK TIMELINE")
                if "Reason:" in timeline.summary:
                    reason = timeline.summary.split("Reason:")[1].split(".")[0]
                    logger.error(f"Fallback reason: {reason}")
            else:
                logger.info("\n✅ TIMELINE V2.0 WORKING!")
                
            # Show sample events
            logger.info("\nSample timeline events:")
            for i, event in enumerate(timeline.events[:5]):
                logger.info(f"{i+1}. {event.description[:100]}...")
                logger.info(f"   Date: {event.timestamp}")
                logger.info(f"   Source: {event.date_source}")
                
        else:
            logger.error("❌ No timeline found in collection")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        

if __name__ == "__main__":
    asyncio.run(test_timeline_v2_debug()) 