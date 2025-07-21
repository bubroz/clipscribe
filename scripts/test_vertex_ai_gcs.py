#!/usr/bin/env python3
"""Test script for Vertex AI integration using pre-uploaded GCS videos."""

import os
# Force Vertex AI mode BEFORE any imports
os.environ["USE_VERTEX_AI"] = "true"

import sys
import asyncio
import logging
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from clipscribe.retrievers.vertex_ai_transcriber import VertexAITranscriber
from clipscribe.retrievers.transcriber import Transcriber
from clipscribe.config.settings import settings


async def test_vertex_ai_with_gcs():
    """Test Vertex AI with pre-uploaded GCS videos."""
    
    # Load pre-uploaded videos
    summary_file = Path("output/pre_uploaded_videos/upload_summary.json")
    with open(summary_file, 'r') as f:
        upload_data = json.load(f)
    
    # Select test videos
    test_videos = [
        {
            "name": "Pegasus Spyware Investigation",
            "url": "https://www.youtube.com/watch?v=6ZVj1_SE4Mo",
            "gcs_uri": "gs://prismatic-iris-429006-g6-clipscribe-staging/videos/2025-07-20T22:12:47.166904/youtube video 6ZVj1_SE4Mo-6ZVj1_SE4Mo.mp4"
        },
        {
            "name": "CNN Town Hall",
            "url": "https://www.youtube.com/watch?v=bdk6o7CUlXY",
            "gcs_uri": "gs://prismatic-iris-429006-g6-clipscribe-staging/videos/2025-07-20T22:27:38.836142/youtube video bdk6o7CUlXY-bdk6o7CUlXY.mp4"
        }
    ]
    
    logger.info("Testing Vertex AI with pre-uploaded GCS videos...")
    logger.info(f"USE_VERTEX_AI environment: {os.getenv('USE_VERTEX_AI')}")
    
    # Create transcriber
    transcriber = Transcriber(
        gemini_model=settings.gemini_model,
        temperature=settings.temperature,
        api_key=settings.google_api_key
    )
    
    for video in test_videos:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {video['name']}")
        logger.info(f"GCS URI: {video['gcs_uri']}")
        
        try:
            # Process directly from GCS
            result = await transcriber.transcribe_audio(
                audio_file=None,  # No local file
                gcs_uri=video['gcs_uri'],
                mode="video"  # Process as video, not audio
            )
            
            if result:
                logger.info("✅ Vertex AI processing successful!")
                logger.info(f"Transcript length: {len(result.get('transcript', ''))} characters")
                logger.info(f"Found {len(result.get('entities', []))} entities")
                logger.info(f"Found {len(result.get('relationships', []))} relationships")
                
                # Show sample of transcript
                transcript = result.get('transcript', '')
                if transcript:
                    logger.info(f"Transcript preview: {transcript[:200]}...")
                
                # Show some entities
                entities = result.get('entities', [])
                if entities:
                    logger.info("Sample entities:")
                    for entity in entities[:5]:
                        logger.info(f"  - {entity.get('name', 'Unknown')} ({entity.get('type', 'Unknown')})")
                
                # Show temporal intelligence
                temporal = result.get('temporal_intelligence', {})
                if temporal:
                    logger.info(f"Timeline events: {len(temporal.get('timeline_events', []))}")
                    logger.info(f"Visual dates: {len(temporal.get('visual_dates', []))}")
            else:
                logger.error("❌ No result returned")
                
        except Exception as e:
            logger.error(f"❌ Failed to process {video['name']}: {e}")
            logger.exception("Full error traceback:")
            continue
    
    return True


async def test_direct_vertex_api():
    """Test direct Vertex AI API call to debug 400 error."""
    logger.info("\n" + "="*60)
    logger.info("Testing direct Vertex AI API call...")
    
    # Create Vertex AI transcriber directly
    vertex_transcriber = VertexAITranscriber()
    
    # Use a small test video
    test_gcs_uri = "gs://prismatic-iris-429006-g6-clipscribe-staging/videos/2025-07-20T22:40:58.589788/youtube video hj9rK35ucCc-hj9rK35ucCc.mp4"
    logger.info(f"Test GCS URI: {test_gcs_uri}")
    
    try:
        # Test with video mode
        logger.info("Testing with video mode...")
        result = await vertex_transcriber.transcribe_with_vertex(
            gcs_uri=test_gcs_uri,
            mode="video"
        )
        logger.info("✅ Video mode successful!")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result preview: {str(result)[:200]}...")
        
    except Exception as e:
        logger.error(f"❌ Video mode failed: {e}")
        logger.exception("Full error:")
        
        # Try audio mode
        logger.info("\nTesting with audio mode...")
        try:
            # Convert to audio-only GCS URI (would need actual conversion)
            audio_gcs_uri = test_gcs_uri.replace('.mp4', '.mp3')
            result = await vertex_transcriber.transcribe_with_vertex(
                gcs_uri=audio_gcs_uri,
                mode="audio"
            )
            logger.info("✅ Audio mode successful!")
            
        except Exception as e2:
            logger.error(f"❌ Audio mode also failed: {e2}")


if __name__ == "__main__":
    logger.info("Starting Vertex AI GCS tests...")
    
    # Test 1: Using pre-uploaded videos through main flow
    success = asyncio.run(test_vertex_ai_with_gcs())
    
    # Test 2: Direct API call to debug
    asyncio.run(test_direct_vertex_api())
    
    if success:
        print("\n✅ Vertex AI GCS test completed!")
    else:
        print("\n❌ Vertex AI GCS test had errors!") 