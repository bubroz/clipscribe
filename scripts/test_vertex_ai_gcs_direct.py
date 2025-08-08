#!/usr/bin/env python3
"""Direct test of Vertex AI to debug 400 error."""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress noisy logs
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


async def test_vertex_ai_direct():
    """Test Vertex AI directly with minimal setup."""
    
    # Import here to ensure environment is set up
    from clipscribe.retrievers.vertex_ai_transcriber import VertexAITranscriber
    
    # Create transcriber
    logger.info("Creating Vertex AI transcriber...")
    transcriber = VertexAITranscriber()
    
    # Test with a pre-uploaded video
    test_gcs_uri = "gs://prismatic-iris-429006-g6-clipscribe-staging/videos/2025-07-20T22:40:58.589788/youtube video hj9rK35ucCc-hj9rK35ucCc.mp4"
    
    logger.info(f"Testing with GCS URI: {test_gcs_uri}")
    
    try:
        # Call Vertex AI directly
        result = await transcriber.transcribe_with_vertex(
            gcs_uri=test_gcs_uri,
            mode="video",
            enhance_transcript=False
        )
        
        logger.info(" Success!")
        logger.info(f"Transcript: {result.get('transcript', {}).get('full_text', '')[:200]}...")
        logger.info(f"Entities: {len(result.get('entities', []))}")
        logger.info(f"Relationships: {len(result.get('relationships', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f" Failed: {e}")
        logger.exception("Full traceback:")
        
        # Try to get more details
        if hasattr(e, 'response'):
            logger.error(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"Response text: {getattr(e.response, 'text', 'N/A')}")
        
        return False


if __name__ == "__main__":
    success = asyncio.run(test_vertex_ai_direct())
    
    if success:
        print("\n Vertex AI test successful!")
    else:
        print("\n Vertex AI test failed!") 