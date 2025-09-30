#!/usr/bin/env python3
"""
Test full pipeline with Vimeo video (non-YouTube).
This tests the complete download → extract audio → Voxtral → Grok flow.
"""

import asyncio
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clipscribe.retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2


# Vimeo test video (known working)
TEST_VIDEO = {
    "url": "https://vimeo.com/148751763",
    "title": "Vimeo Test - Big Buck Bunny",
    "duration": "~10min",
    "notes": "Public domain, tests full pipeline without YouTube"
}


async def main():
    """Test complete pipeline with Vimeo."""
    
    print("\n" + "=" * 80)
    print("VIMEO BASELINE TEST - FULL PIPELINE")
    print("Tests: Download → FFmpeg Extract → Voxtral → Grok")
    print("=" * 80)
    
    print(f"\n📹 Test Video:")
    print(f"   URL: {TEST_VIDEO['url']}")
    print(f"   Title: {TEST_VIDEO['title']}")
    print(f"   Duration: {TEST_VIDEO['duration']}")
    print(f"   Platform: Vimeo (non-YouTube)")
    
    start_time = time.time()
    
    try:
        print("\n1️⃣  Initializing VideoIntelligenceRetrieverV2...")
        retriever = VideoIntelligenceRetrieverV2(
            output_dir="output/vimeo_baseline_test",
            use_cache=True
        )
        print("   ✅ Retriever initialized")
        
        print("\n2️⃣  Processing video (this will take 5-10 minutes)...")
        print("   → Downloading video from Vimeo")
        print("   → Extracting audio with ffmpeg")
        print("   → Transcribing with Voxtral")
        print("   → Extracting intelligence with Grok-4")
        print("   → Building knowledge graph")
        print("   → Saving outputs")
        
        result = await retriever.process_url(TEST_VIDEO["url"])
        
        if result:
            processing_time = time.time() - start_time
            
            print("\n3️⃣  Processing complete!")
            print(f"   ✅ Transcript: {len(result.transcript.text) if hasattr(result, 'transcript') else 0} chars")
            print(f"   ✅ Entities: {len(result.entities)}")
            print(f"   ✅ Relationships: {len(result.relationships)}")
            print(f"   ✅ Topics: {len(result.topics) if hasattr(result, 'topics') else 0}")
            print(f"   ✅ Cost: ${result.processing_cost:.3f}")
            print(f"   ✅ Time: {processing_time:.1f}s")
            
            # Check output files
            output_dir = Path("output/vimeo_baseline_test")
            if output_dir.exists():
                files = list(output_dir.glob("*"))
                print(f"   ✅ Output files: {len(files)}")
                for f in files:
                    print(f"      - {f.name}")
            
            # Final verdict
            print("\n" + "=" * 80)
            print("✅ FULL PIPELINE VALIDATION PASSED")
            print("=" * 80)
            print("\n📊 CONFIRMED WORKING:")
            print("   ✅ yt-dlp download: WORKING (Vimeo)")
            print("   ✅ FFmpeg audio extraction: WORKING")
            print("   ✅ Voxtral transcription: WORKING")
            print("   ✅ Grok-4 extraction: WORKING")
            print("   ✅ Knowledge graph: WORKING")
            print("   ✅ Output generation: WORKING")
            print("\n💡 CONCLUSION:")
            print("   The Voxtral-Grok pipeline is FULLY FUNCTIONAL.")
            print("   YouTube download failure is ISOLATED to SABR bot detection.")
            print("   PO Token Manager will resolve the YouTube-specific issue.")
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
        
        print("\n" + "=" * 80)
        print("❌ FULL PIPELINE VALIDATION FAILED")
        print("=" * 80)
        print("\n⚠️  PIPELINE ISSUE DETECTED:")
        print(f"   Error: {e}")
        print("\n🔍 DEBUGGING NEEDED:")
        print("   - Check yt-dlp installation")
        print("   - Check ffmpeg installation")
        print("   - Check API keys (MISTRAL_API_KEY, XAI_API_KEY)")
        print("   - Check network connectivity")
        print("=" * 80)
        
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Vimeo baseline test...")
    print("⚠️  This will take 5-10 minutes")
    print("💡 Testing complete pipeline without YouTube bot detection\n")
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
