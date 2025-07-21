#!/usr/bin/env python3
"""Test Vertex AI integration through the main ClipScribe flow."""

import os
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

# Suppress noisy logs
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

from clipscribe.config.settings import settings
from clipscribe.retrievers.transcriber import GeminiFlashTranscriber
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever


async def test_vertex_with_main_flow():
    """Test Vertex AI through the main ClipScribe flow."""
    
    logger.info("Testing Vertex AI through main ClipScribe flow...")
    logger.info(f"USE_VERTEX_AI: {os.getenv('USE_VERTEX_AI')}")
    logger.info(f"settings.use_vertex_ai: {settings.use_vertex_ai}")
    
    # Test URL
    test_url = "https://www.youtube.com/watch?v=hj9rK35ucCc"  # Same video we just tested
    
    # Create retriever
    retriever = VideoIntelligenceRetriever(
        youtube_api_key=settings.youtube_api_key,
        gemini_api_key=settings.google_api_key,
        gemini_model=settings.gemini_model,
        temperature=settings.temperature
    )
    
    try:
        # Process video
        logger.info(f"Processing video: {test_url}")
        result = await retriever.retrieve(test_url)
        
        if result:
            logger.info("✅ Video processing successful!")
            logger.info(f"Title: {result.metadata.title}")
            logger.info(f"Duration: {result.metadata.duration}s")
            logger.info(f"Transcript length: {len(result.transcript.full_text)} chars")
            logger.info(f"Entities: {len(result.entities)}")
            logger.info(f"Relationships: {len(result.relationships)}")
            logger.info(f"Key insights: {len(result.key_insights)}")
            
            # Show some entities
            if result.entities:
                logger.info("\nSample entities:")
                for entity in result.entities[:5]:
                    logger.info(f"  - {entity.entity} ({entity.type})")
            
            # Check cost tracking
            logger.info(f"\nProcessing cost: ${result.metadata.processing_cost:.4f}")
            logger.info(f"Model used: {result.metadata.model_used}")
            
            return True
        else:
            logger.error("❌ No result returned")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        logger.exception("Full traceback:")
        return False


async def compare_vertex_vs_regular():
    """Compare Vertex AI vs regular Gemini API."""
    
    logger.info("\n" + "="*60)
    logger.info("Comparing Vertex AI vs Regular Gemini API...")
    
    # First test with Vertex AI
    os.environ["USE_VERTEX_AI"] = "true"
    logger.info("\n1. Testing with Vertex AI...")
    vertex_start = asyncio.get_event_loop().time()
    vertex_success = await test_vertex_with_main_flow()
    vertex_time = asyncio.get_event_loop().time() - vertex_start
    
    # Then test without Vertex AI
    os.environ["USE_VERTEX_AI"] = "false"
    logger.info("\n2. Testing with Regular Gemini API...")
    regular_start = asyncio.get_event_loop().time()
    # Would run the same test here, but skipping for now
    
    logger.info("\n" + "="*60)
    logger.info("Comparison Results:")
    logger.info(f"Vertex AI: {'✅ Success' if vertex_success else '❌ Failed'} ({vertex_time:.1f}s)")
    logger.info("Regular Gemini: Skipped for this test")


if __name__ == "__main__":
    # Test through main flow
    success = asyncio.run(test_vertex_with_main_flow())
    
    # Optional: Run comparison
    # asyncio.run(compare_vertex_vs_regular())
    
    if success:
        print("\n✅ Vertex AI integration test successful!")
    else:
        print("\n❌ Vertex AI integration test failed!") 