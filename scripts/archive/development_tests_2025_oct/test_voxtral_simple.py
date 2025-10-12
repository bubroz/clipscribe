#!/usr/bin/env python3
"""Simple test to isolate Voxtral transcription issue."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["XAI_API_KEY"] = "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr"
os.environ["USE_VOXTRAL"] = "true"

from src.clipscribe.utils.logging import setup_logging
from src.clipscribe.processors.hybrid_processor import HybridProcessor
import logging

setup_logging(level="DEBUG")
logger = logging.getLogger(__name__)


async def main():
    """Test Voxtral with a short video."""
    
    print("Testing Voxtral transcription...")
    
    processor = HybridProcessor(
        voxtral_model="voxtral-mini-2507",
        grok_model="grok-4-0709"
    )
    
    # Use a short test video
    test_url = "https://www.youtube.com/watch?v=3p2NaXyZy4U"
    
    try:
        # Create mock metadata for testing
        metadata = {
            "video_id": "3p2NaXyZy4U",
            "title": "Test Video",
            "channel": "Test Channel",
            "channel_id": "test",
            "duration": 5320,
            "url": test_url,
            "description": "Test",
            "published_at": "2024-01-01"
        }
        
        # Download audio first
        from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
        client = EnhancedUniversalVideoClient()
        
        print("Downloading audio...")
        audio_path, real_metadata = await client.download_audio(test_url)
        print(f"Audio downloaded: {audio_path}")
        
        # Update metadata with real values
        metadata.update({
            "title": real_metadata.title,
            "channel": real_metadata.channel,
            "duration": real_metadata.duration,
        })
        
        print(f"\nProcessing {real_metadata.duration}s video...")
        print("This will:")
        print("1. Chunk into ~14-minute segments")
        print("2. Transcribe each chunk with Voxtral")
        print("3. Merge transcripts")
        print("4. Extract intelligence with Grok-4")
        
        # Process with full pipeline
        result = await processor.process_video(
            audio_path,
            metadata,
            force_reprocess=True
        )
        
        if result:
            print(f"\n✅ SUCCESS!")
            print(f"Entities: {len(result.entities)}")
            print(f"Relationships: {len(result.relationships)}")
            print(f"Cost: ${result.processing_cost:.4f}")
        else:
            print("\n❌ FAILED - No result returned")
            
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {e}")
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
