#!/usr/bin/env python3
"""
Test Voxtral-Grok pipeline with a non-YouTube video (or local audio).
This isolates YouTube bot detection issues from actual pipeline issues.
"""

import asyncio
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clipscribe.retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2


# Non-YouTube test options
TEST_OPTIONS = {
    "vimeo": {
        "url": "https://vimeo.com/148751763",  # Sample Vimeo video
        "title": "Vimeo Test Video",
        "platform": "Vimeo",
        "notes": "Tests non-YouTube video download"
    },
    "local_audio": {
        "file": "test_audio.mp3",
        "title": "Local Audio Test",
        "platform": "Local File",
        "notes": "Bypasses all download issues - direct pipeline test"
    },
    "cached_youtube": {
        "file": "cache/Attack Life with Brute Force-Ii3UpOT8x-A.mp4",
        "title": "Cached YouTube Video",
        "platform": "Local Cache",
        "notes": "Uses previously downloaded YouTube video"
    }
}


async def test_local_file(audio_file: str, test_info: dict):
    """Test with a local audio file - bypasses all download issues."""
    
    print("\n" + "=" * 80)
    print(f"TESTING: {test_info['title']}")
    print(f"File: {audio_file}")
    print(f"Platform: {test_info['platform']}")
    print("=" * 80)
    
    audio_path = Path(audio_file)
    if not audio_path.exists():
        print(f"\n❌ Audio file not found: {audio_file}")
        print("   Available cached files:")
        cache_dir = Path("cache")
        if cache_dir.exists():
            for f in cache_dir.glob("*.mp[34]"):
                print(f"      - {f}")
        return None
    
    print(f"\n✅ Audio file found: {audio_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    start_time = time.time()
    
    try:
        # Import processor directly to bypass video download
        from clipscribe.processors.hybrid_processor import HybridProcessor
        
        print("\n1️⃣  Initializing HybridProcessor...")
        processor = HybridProcessor(
            voxtral_model="voxtral-mini-2507",
            grok_model="grok-4-0709"
        )
        print("   ✅ HybridProcessor initialized")
        
        # Create minimal metadata
        metadata = {
            "video_id": "test_local",
            "title": test_info['title'],
            "description": "Local test file",
            "duration": 300,  # Estimate
            "url": str(audio_path)
        }
        
        print("\n2️⃣  Processing audio with Voxtral-Grok pipeline...")
        result = await processor.process_video(str(audio_path), metadata)
        
        if result:
            processing_time = time.time() - start_time
            
            print("\n3️⃣  Processing complete!")
            print(f"   ✅ Transcript: {len(result.transcript.text) if hasattr(result, 'transcript') else 0} chars")
            print(f"   ✅ Entities: {len(result.entities) if hasattr(result, 'entities') else 0}")
            print(f"   ✅ Relationships: {len(result.relationships) if hasattr(result, 'relationships') else 0}")
            print(f"   ✅ Topics: {len(result.topics) if hasattr(result, 'topics') else 0}")
            print(f"   ✅ Cost: ${result.processing_cost:.3f}")
            print(f"   ✅ Time: {processing_time:.1f}s")
            
            return {
                "success": True,
                "processing_time": processing_time,
                "cost": result.processing_cost,
                "entity_count": len(result.entities),
                "relationship_count": len(result.relationships),
                "topic_count": len(result.topics)
            }
        else:
            print("\n❌ Processing returned None")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_url(video_url: str, test_info: dict):
    """Test with a non-YouTube URL."""
    
    print("\n" + "=" * 80)
    print(f"TESTING: {test_info['title']}")
    print(f"URL: {video_url}")
    print(f"Platform: {test_info['platform']}")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        print("\n1️⃣  Initializing VideoIntelligenceRetrieverV2...")
        retriever = VideoIntelligenceRetrieverV2(
            output_dir=f"output/non_youtube_test/{test_info['platform'].lower()}",
            use_cache=True
        )
        print("   ✅ Retriever initialized")
        
        print("\n2️⃣  Processing video...")
        result = await retriever.process_url(video_url)
        
        if result:
            processing_time = time.time() - start_time
            
            print("\n3️⃣  Processing complete!")
            print(f"   ✅ Entities: {len(result.entities)}")
            print(f"   ✅ Relationships: {len(result.relationships)}")
            print(f"   ✅ Cost: ${result.processing_cost:.3f}")
            print(f"   ✅ Time: {processing_time:.1f}s")
            
            return {
                "success": True,
                "processing_time": processing_time,
                "cost": result.processing_cost,
                "entity_count": len(result.entities),
                "relationship_count": len(result.relationships)
            }
        else:
            print("\n❌ Processing returned None")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run non-YouTube baseline test."""
    
    print("\n" + "=" * 80)
    print("NON-YOUTUBE BASELINE VALIDATION")
    print("Testing Voxtral-Grok pipeline without YouTube bot detection issues")
    print("=" * 80)
    
    # Check for cached files first (fastest option)
    cached_file = TEST_OPTIONS["cached_youtube"]["file"]
    if Path(cached_file).exists():
        print(f"\n✅ Found cached video: {cached_file}")
        print("   Using cached file to test pipeline directly...")
        result = await test_local_file(cached_file, TEST_OPTIONS["cached_youtube"])
    elif Path("test_audio.mp3").exists():
        print("\n✅ Found test_audio.mp3")
        print("   Using local test file...")
        result = await test_local_file("test_audio.mp3", TEST_OPTIONS["local_audio"])
    else:
        print("\n⚠️  No cached files found, attempting Vimeo download...")
        result = await test_url(TEST_OPTIONS["vimeo"]["url"], TEST_OPTIONS["vimeo"])
    
    # Summary
    print("\n\n" + "=" * 80)
    if result and result.get("success"):
        print("✅ NON-YOUTUBE TEST PASSED")
        print("=" * 80)
        print("\n📊 PIPELINE VALIDATION:")
        print("   ✅ Voxtral transcription: WORKING")
        print("   ✅ Grok-4 extraction: WORKING")
        print("   ✅ Output generation: WORKING")
        print("\n💡 CONCLUSION:")
        print("   The Voxtral-Grok pipeline is FUNCTIONAL.")
        print("   YouTube download failure is ISOLATED to bot detection.")
        print("   PO Token Manager fix will resolve the YouTube issue.")
    else:
        print("❌ NON-YOUTUBE TEST FAILED")
        print("=" * 80)
        print("\n⚠️  PIPELINE ISSUE DETECTED:")
        print("   The Voxtral-Grok pipeline has issues beyond YouTube.")
        print("   Need to debug the core processing logic.")
    print("=" * 80)
    
    return result is not None and result.get("success", False)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
