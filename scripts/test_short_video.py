#!/usr/bin/env python3
"""Test with a SHORT controversial video to validate the pipeline."""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["XAI_API_KEY"] = "xai-QlxLU3aSN0EYKt1HnVmOUz3l05v12DkowN2qvAIDsox61KGyMEqV92SMeaQ8PU4voX8WHEBmS7p5T5Fr"
os.environ["USE_VOXTRAL"] = "true"

from src.clipscribe.utils.logging import setup_logging
from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
from src.clipscribe.processors.hybrid_processor import HybridProcessor
import logging

setup_logging(level="INFO")
logger = logging.getLogger(__name__)


async def main():
    """Test with a SHORT video (< 10 minutes)."""
    
    print("="*80)
    print("TESTING WITH SHORT VIDEO")
    print("="*80)
    
    # Use a SHORT controversial video from our test list
    # Whatifalthist video is 4131 seconds (68 minutes) - still too long
    # Let's use a test video that's under 10 minutes
    
    # First, let's check video durations
    test_videos = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "Rick Roll - 3:32"),  # 212 seconds
    ]
    
    processor = HybridProcessor(
        voxtral_model="voxtral-mini-2507",
        grok_model="grok-4-0709"
    )
    
    for url, description in test_videos:
        print(f"\n📹 Testing: {description}")
        print(f"URL: {url}")
        
        start_time = time.time()
        
        try:
            # Download audio
            client = EnhancedUniversalVideoClient()
            audio_path, metadata = await client.download_audio(url)
            
            print(f"✅ Downloaded: {metadata.title}")
            print(f"   Duration: {metadata.duration}s ({metadata.duration/60:.1f} min)")
            
            # Process with hybrid pipeline
            metadata_dict = {
                "video_id": metadata.video_id,
                "title": metadata.title,
                "channel": metadata.channel,
                "channel_id": metadata.channel_id or "unknown",
                "duration": metadata.duration,
                "url": url,
                "description": metadata.description or "",
                "published_at": metadata.published_at
            }
            
            print("\n🔄 Processing with Voxtral → Grok-4...")
            result = await processor.process_video(
                audio_path,
                metadata_dict,
                force_reprocess=True
            )
            
            processing_time = time.time() - start_time
            
            if result and result.entities:
                print(f"\n✅ SUCCESS!")
                print(f"   • Entities: {len(result.entities)}")
                print(f"   • Relationships: {len(result.relationships)}")
                print(f"   • Topics: {len(result.topics)}")
                print(f"   • Processing time: {processing_time:.1f}s")
                print(f"   • Cost: ${result.processing_cost:.4f}")
                
                # Sample entities
                print(f"\n   Sample entities:")
                for e in result.entities[:5]:
                    print(f"   - {e.name} ({e.type})")
            else:
                print(f"\n⚠️ WARNING: No entities extracted")
                print(f"   Processing time: {processing_time:.1f}s")
                
        except Exception as e:
            import traceback
            print(f"\n❌ ERROR: {e}")
            print(traceback.format_exc())
    
    print("\n" + "="*80)
    print("✨ TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
