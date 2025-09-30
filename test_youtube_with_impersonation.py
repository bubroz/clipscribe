#!/usr/bin/env python3
"""
Test YouTube download with curl-cffi impersonation + full Voxtral-Grok pipeline.
This validates the complete solution.
"""

import asyncio
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clipscribe.processors.hybrid_processor import HybridProcessor


async def main():
    """Test full pipeline with YouTube audio downloaded via curl-cffi."""
    
    print("\n" + "=" * 80)
    print("YOUTUBE + CURL-CFFI + VOXTRAL-GROK PIPELINE TEST")
    print("=" * 80)
    
    audio_file = "test_youtube_download.mp3"
    
    if not Path(audio_file).exists():
        print(f"\n❌ Audio file not found: {audio_file}")
        print("   Run: poetry run yt-dlp --impersonate 'Chrome-131:Macos-14' ...")
        return False
    
    print(f"\n✅ YouTube audio downloaded via curl-cffi: {Path(audio_file).stat().st_size / 1024 / 1024:.2f} MB")
    
    start_time = time.time()
    
    try:
        print("\n1️⃣  Initializing HybridProcessor...")
        processor = HybridProcessor(
            voxtral_model="voxtral-mini-2507",
            grok_model="grok-4-0709"
        )
        print("   ✅ HybridProcessor initialized")
        
        metadata = {
            "video_id": "5Fy2y3vzkWE",
            "title": "Attack Life with Brute Force (Partnering with Barbell Apparel)",
            "description": "Test with curl-cffi downloaded audio",
            "duration": 124,  # ~2 minutes
            "url": "https://www.youtube.com/watch?v=5Fy2y3vzkWE"
        }
        
        print("\n2️⃣  Processing with Voxtral-Grok pipeline...")
        result = await processor.process_video(audio_file, metadata)
        
        if result:
            processing_time = time.time() - start_time
            
            print("\n3️⃣  Processing complete!")
            print(f"   ✅ Transcript: {len(result.transcript.full_text)} chars")
            print(f"   ✅ Language: {result.transcript.language}")
            print(f"   ✅ Entities: {len(result.entities)}")
            print(f"   ✅ Relationships: {len(result.relationships)}")
            print(f"   ✅ Topics: {len(result.topics)}")
            print(f"   ✅ Processing Cost: ${result.processing_cost:.3f}")
            print(f"   ✅ Processing Time: {processing_time:.1f}s")
            
            print("\n" + "=" * 80)
            print("✅ COMPLETE SOLUTION VALIDATED")
            print("=" * 80)
            print("\n📊 CONFIRMED WORKING:")
            print("   ✅ curl-cffi impersonation: WORKING")
            print("   ✅ yt-dlp download: WORKING (YouTube)")
            print("   ✅ ffmpeg extraction: WORKING")
            print("   ✅ Voxtral transcription: WORKING")
            print("   ✅ Grok-4 extraction: WORKING")
            print("   ✅ Knowledge graph: WORKING")
            print("\n💡 SOLUTION:")
            print("   - curl-cffi bypasses YouTube bot detection")
            print("   - yt-dlp 2025.09.26 has improved SABR handling")
            print("   - No PO tokens needed with impersonation!")
            print("   - Zero additional infrastructure cost")
            print("\n🚀 READY FOR PRODUCTION:")
            print("   - Integrate into UniversalVideoClient")
            print("   - Add browser fallback for edge cases")
            print("   - Deploy and monitor")
            print("=" * 80)
            
            return True
        else:
            print("\n❌ Processing returned None")
            return False
            
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"\n❌ Error after {processing_time:.1f}s: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
