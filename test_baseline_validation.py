#!/usr/bin/env python3
"""
Baseline Validation Test for ClipScribe v2.51.0
Tests the current committed state with approved test videos.
Run in a separate terminal to avoid IDE timeouts.
"""

import asyncio
import sys
from pathlib import Path
import time
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clipscribe.retrievers.video_retriever_v2 import VideoIntelligenceRetrieverV2
from clipscribe.config.settings import Settings


# Test videos from MASTER_TEST_VIDEO_TABLE.md
TEST_VIDEOS = {
    "short_training": {
        "url": "https://www.youtube.com/watch?v=5Fy2y3vzkWE",
        "title": "Attack Life with Brute Force (Partnering with Barbell Apparel)",
        "duration": "~5min",
        "category": "Professional Training",
        "expected_entities": 10,
        "notes": "Short, clean content - perfect baseline test"
    },
    "medium_osint": {
        "url": "https://www.youtube.com/watch?v=V9VEvGSzzk0",
        "title": "8 Companies Selling Your Personal Data to Cops",
        "duration": "~20min",
        "category": "OSINT/Privacy",
        "expected_entities": 20,
        "notes": "User-submitted, data broker analysis"
    }
}


async def test_single_video(video_key: str, video_info: dict) -> dict:
    """Test a single video and return results."""
    
    print("\n" + "=" * 80)
    print(f"TESTING: {video_info['title']}")
    print(f"URL: {video_info['url']}")
    print(f"Duration: {video_info['duration']}")
    print(f"Category: {video_info['category']}")
    print("=" * 80)
    
    result = {
        "video_key": video_key,
        "success": False,
        "error": None,
        "processing_time": 0,
        "cost": 0,
        "entity_count": 0,
        "relationship_count": 0,
        "output_files": []
    }
    
    start_time = time.time()
    
    try:
        # Initialize retriever
        print("\n1️⃣  Initializing VideoIntelligenceRetrieverV2...")
        output_dir = f"output/baseline_test/{video_key}"
        retriever = VideoIntelligenceRetrieverV2(
            output_dir=output_dir,
            use_cache=True
        )
        print("   ✅ Retriever initialized")
        
        # Process video
        print("\n2️⃣  Processing video...")
        video_result = await retriever.process_url(video_info["url"])
        
        if video_result:
            result["success"] = True
            result["processing_time"] = time.time() - start_time
            result["cost"] = getattr(video_result, 'processing_cost', 0)
            result["entity_count"] = len(video_result.entities) if hasattr(video_result, 'entities') else 0
            result["relationship_count"] = len(video_result.relationships) if hasattr(video_result, 'relationships') else 0
            
            # Check output files
            output_path = Path(output_dir)
            if output_path.exists():
                result["output_files"] = [f.name for f in output_path.glob("*")]
            
            print("\n3️⃣  Processing complete!")
            print(f"   ✅ Entities: {result['entity_count']}")
            print(f"   ✅ Relationships: {result['relationship_count']}")
            print(f"   ✅ Cost: ${result['cost']:.3f}")
            print(f"   ✅ Time: {result['processing_time']:.1f}s")
            print(f"   ✅ Output files: {len(result['output_files'])}")
        else:
            result["error"] = "Processing returned None"
            print("\n   ❌ Processing returned None")
            
    except Exception as e:
        result["error"] = str(e)
        result["processing_time"] = time.time() - start_time
        print(f"\n   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return result


async def run_baseline_tests():
    """Run all baseline tests."""
    
    print("\n" + "=" * 80)
    print("CLIPSCRIBE v2.51.0 BASELINE VALIDATION")
    print("Testing current committed state with approved test videos")
    print("=" * 80)
    
    # Check environment
    print("\n📋 Pre-flight checks:")
    import os
    
    mistral_key = os.getenv("MISTRAL_API_KEY")
    xai_key = os.getenv("XAI_API_KEY")
    
    if not mistral_key:
        print("   ❌ MISTRAL_API_KEY not set")
        return False
    print("   ✅ MISTRAL_API_KEY found")
    
    if not xai_key:
        print("   ❌ XAI_API_KEY not set")
        return False
    print("   ✅ XAI_API_KEY found")
    
    # Run tests
    results = []
    
    # Test 1: Short video (quick validation)
    print("\n\n" + "🎯" * 40)
    print("TEST 1: SHORT VIDEO (BASELINE)")
    print("🎯" * 40)
    result1 = await test_single_video("short_training", TEST_VIDEOS["short_training"])
    results.append(result1)
    
    # Only proceed to longer video if short one works
    if result1["success"]:
        print("\n\n" + "🎯" * 40)
        print("TEST 2: MEDIUM VIDEO (OSINT CONTENT)")
        print("🎯" * 40)
        result2 = await test_single_video("medium_osint", TEST_VIDEOS["medium_osint"])
        results.append(result2)
    else:
        print("\n\n⚠️  Skipping medium video test due to short video failure")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("BASELINE TEST SUMMARY")
    print("=" * 80)
    
    successes = sum(1 for r in results if r["success"])
    failures = len(results) - successes
    total_cost = sum(r["cost"] for r in results)
    total_time = sum(r["processing_time"] for r in results)
    
    print(f"\n📊 Results:")
    print(f"   Tests Run: {len(results)}")
    print(f"   ✅ Passed: {successes}")
    print(f"   ❌ Failed: {failures}")
    print(f"   💰 Total Cost: ${total_cost:.3f}")
    print(f"   ⏱️  Total Time: {total_time:.1f}s")
    
    print(f"\n📝 Detailed Results:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"\n   {status} - {result['video_key']}")
        if result["success"]:
            print(f"      Entities: {result['entity_count']}")
            print(f"      Relationships: {result['relationship_count']}")
            print(f"      Cost: ${result['cost']:.3f}")
            print(f"      Time: {result['processing_time']:.1f}s")
            print(f"      Files: {len(result['output_files'])}")
        else:
            print(f"      Error: {result['error']}")
    
    # Save results
    results_file = Path("output/baseline_test/results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")
    
    # Final verdict
    print("\n" + "=" * 80)
    if failures == 0:
        print("✅ BASELINE VALIDATION PASSED")
        print("Current v2.51.0 state is working correctly!")
        print("Safe to review and merge uncommitted changes.")
    else:
        print("❌ BASELINE VALIDATION FAILED")
        print("Current v2.51.0 state has issues!")
        print("Do NOT merge uncommitted changes until baseline is fixed.")
    print("=" * 80)
    
    return failures == 0


if __name__ == "__main__":
    print("\n🚀 Starting baseline validation...")
    print("⚠️  This will take 5-20 minutes depending on video lengths")
    print("💡 Watch progress in this terminal window\n")
    
    success = asyncio.run(run_baseline_tests())
    sys.exit(0 if success else 1)
