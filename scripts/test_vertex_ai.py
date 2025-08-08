#!/usr/bin/env python3
"""Test script for Vertex AI integration."""

import os
# Force Vertex AI mode BEFORE any imports
os.environ["USE_VERTEX_AI"] = "true"

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever


async def test_vertex_ai():
    """Test Vertex AI integration with a sample video."""
    # Test video URL - PBS NewsHour segment (better for entity extraction)
    test_url = "https://www.youtube.com/watch?v=6ZVj1_SE4Mo&t=65s"  # Pegasus Spyware Investigation Part 1
    
    logger.info("Testing Vertex AI integration...")
    logger.info(f"Test URL: {test_url}")
    logger.info("Using PBS NewsHour content for better entity extraction demonstration")
    logger.info(f"USE_VERTEX_AI environment: {os.getenv('USE_VERTEX_AI')}")
    
    try:
        # Create retriever (it will use Vertex AI based on environment)
        retriever = VideoIntelligenceRetriever(
            mode="audio",  # Using audio mode to avoid large video upload timeouts
            use_cache=False  # Don't use cache for this test
        )
        
        # Process video - use process_url which returns VideoIntelligence
        logger.info("Processing video with Vertex AI...")
        result = await retriever.process_url(test_url)
        
        if not result:
            logger.error(" No result returned from process_url")
            return False
        
        # Log results
        logger.info(" Vertex AI processing successful!")
        logger.info(f"Transcript length: {len(result.transcript.full_text)} characters")
        logger.info(f"Found {len(result.entities)} entities")
        logger.info(f"Found {len(result.relationships)} relationships")
        
        # Show sample of transcript
        if result.transcript.full_text:
            logger.info(f"Transcript preview: {result.transcript.full_text[:200]}...")
        
        # Show some entities
        if result.entities:
            logger.info("Sample entities:")
            for entity in result.entities[:5]:
                logger.info(f"  - {entity.entity} ({entity.type})")
        
        # Show processing cost
        logger.info(f"Processing cost: ${result.processing_cost:.4f}")
        
        # Show temporal intelligence
        if hasattr(result, 'temporal_intelligence') and result.temporal_intelligence:
            logger.info(f"Temporal events: {len(result.temporal_intelligence.timeline_events)}")
            logger.info(f"Visual dates: {len(result.temporal_intelligence.visual_dates)}")
        
        return True
        
    except Exception as e:
        logger.error(f" Vertex AI test failed: {e}")
        logger.exception("Full error traceback:")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_vertex_ai())
    if success:
        print("\n Vertex AI integration test passed!")
        sys.exit(0)
    else:
        print("\n Vertex AI integration test failed!")
        sys.exit(1) 