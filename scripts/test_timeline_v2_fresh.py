#!/usr/bin/env python3
"""Test Timeline v2.0 with fresh video processing (no cache)"""

import asyncio
import logging
import sys
import os
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
        logging.FileHandler('timeline_v2_fresh.log')
    ]
)
logger = logging.getLogger(__name__)

# Focus on timeline components
logging.getLogger('src.clipscribe.timeline').setLevel(logging.DEBUG)
logging.getLogger('src.clipscribe.extractors.multi_video_processor').setLevel(logging.DEBUG)


async def test_timeline_v2_fresh():
    """Test Timeline v2.0 with fresh video processing"""
    logger.info("=" * 60)
    logger.info("Timeline v2.0 Fresh Test (No Cache)")
    logger.info("=" * 60)
    
    # Use both PBS Pegasus videos from the master test table
    test_urls = [
        "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",  # Pegasus Part 1
        "https://www.youtube.com/watch?v=xYMWTXIkANM"   # Pegasus Part 2
    ]
    
    try:
        # Disable cache for fresh processing
        retriever = VideoIntelligenceRetriever(
            use_advanced_extraction=True,
            use_cache=False  # Force fresh processing
        )
        
        videos = []
        for url in test_urls:
            logger.info(f"\n{'='*40}")
            logger.info(f"Processing FRESH video (no cache): {url}")
            video = await retriever.process_url(url)
            
            if video:
                logger.info(f"✅ Video processed successfully")
                logger.info(f"   - Title: {video.metadata.title}")
                logger.info(f"   - Entities: {len(video.entities)}")
                logger.info(f"   - Key Points: {len(video.key_points)}")
                
                # Check transcript
                if hasattr(video, 'transcript') and video.transcript:
                    logger.info(f"   - Transcript length: {len(video.transcript.full_text)} chars")
                    logger.info(f"   - First 100 chars: {video.transcript.full_text[:100]}...")
                else:
                    logger.error("   - NO TRANSCRIPT FOUND!")
                    
                # Check if Timeline v2.0 data exists
                if hasattr(video, 'timeline_v2'):
                    logger.info(f"   - Timeline v2.0 data: {bool(video.timeline_v2)}")
                    if video.timeline_v2:
                        logger.info(f"     Status: {video.timeline_v2.get('status')}")
                        logger.info(f"     Events: {video.timeline_v2.get('temporal_events_count', 0)}")
                else:
                    logger.warning("   - No timeline_v2 attribute found")
                    
                # Show sample entities with timestamps
                if video.entities:
                    logger.info("   - Sample entities with timestamps:")
                    for entity in video.entities[:5]:
                        logger.info(f"     • {entity.name} ({entity.type}) - timestamp: {entity.timestamp}, confidence: {entity.confidence}")
                        
                videos.append(video)
            else:
                logger.error(f"❌ Failed to process video: {url}")
                
        if len(videos) < 2:
            logger.error("Not enough videos for collection processing")
            return
            
        # Process collection with both videos to test Timeline v2.0
        logger.info(f"\n{'='*60}")
        logger.info("Testing Timeline v2.0 with fresh Pegasus series...")
        
        processor = MultiVideoProcessor(use_ai_validation=True)
        collection = await processor.process_video_collection(
            videos=videos,
            collection_type=VideoCollectionType.SERIES,  # These are a series
            collection_title="Pegasus Investigation Timeline v2.0 Fresh Test"
        )
        
        # Check results
        if collection and hasattr(collection, 'consolidated_timeline'):
            timeline = collection.consolidated_timeline
            logger.info(f"\n✅ Timeline v2.0 processed")
            logger.info(f"Timeline ID: {timeline.timeline_id}")
            logger.info(f"Total events: {len(timeline.events)}")
            
            # Check if it's fallback
            if "fallback" in timeline.timeline_id:
                logger.warning("\n⚠️ USING FALLBACK TIMELINE")
                if hasattr(timeline, 'summary') and "Reason:" in timeline.summary:
                    reason = timeline.summary.split("Reason:")[1].split(".")[0]
                    logger.error(f"Fallback reason: {reason}")
            else:
                logger.info("\n✅ TIMELINE V2.0 WORKING!")
                
            # Show timeline events
            if timeline.events:
                logger.info("\nTimeline events:")
                for i, event in enumerate(timeline.events[:10]):  # Show more events
                    logger.info(f"{i+1}. {event.description[:100]}...")
                    logger.info(f"   Date: {event.timestamp}")
                    logger.info(f"   Source: {event.date_source}")
                    logger.info(f"   Confidence: {event.confidence}")
        else:
            logger.error(f"❌ Failed to get timeline from collection")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        

if __name__ == "__main__":
    asyncio.run(test_timeline_v2_fresh()) 