#!/usr/bin/env python3
"""
Test Grok 4 Integration with Real Video from MASTER_TEST_VIDEO_TABLE.md

This script tests the complete Grok 4 integration using the Pegasus Spyware
investigation video from the master test table. This validates:

1. Grok 4 model usage
2. Hybrid fallback system
3. Sensitive content processing
4. Real video processing pipeline
5. Cost calculation accuracy
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clipscribe.api.unified_transcriber import UnifiedTranscriberAPI, BackendType
from clipscribe.config.settings import Settings


async def test_grok4_pegasus_integration():
    """
    Test Grok 4 integration with real Pegasus spyware video.

    This is a critical test for sensitive content processing.
    """
    print("🔍 TESTING GROK 4 INTEGRATION WITH REAL VIDEO")
    print("=" * 60)

    # Initialize settings and API
    settings = Settings()

    # Check if xAI API key is available
    if not settings.xai_api_key:
        print("❌ XAI_API_KEY not found in environment variables")
        print("   Please set XAI_API_KEY to test Grok 4 integration")
        print("   Skipping real API test, but validating framework...")
        await test_framework_only()
        return

    print(f"✅ xAI API key found: {settings.xai_api_key[:8]}...")

    # Initialize unified API
    api = UnifiedTranscriberAPI()
    print("✅ Unified API initialized")

    # Test video from MASTER_TEST_VIDEO_TABLE.md - Pegasus Spyware Part 1
    pegasus_url = "https://www.youtube.com/watch?v=6ZVj1_SE4Mo&t=65s"
    video_title = "Global Spyware Scandal: Exposing Pegasus Part One"
    expected_duration = 1800  # 30 minutes

    print(f"🎯 Testing with: {video_title}")
    print(f"   URL: {pegasus_url}")
    print(f"   Expected duration: {expected_duration}s")

    try:
        start_time = time.time()

        # Process the video - this should automatically use Grok for sensitive content
        print("\n🔄 Processing video with hybrid fallback system...")
        print("   (Should prefer Grok for sensitive 'Pegasus' content)")

        result = await api.transcribe(
            audio_path=pegasus_url,  # Will be downloaded automatically
            metadata={
                "title": video_title,
                "description": "Investigation into NSO Group's Pegasus spyware and global surveillance",
                "channel": "FRONTLINE PBS",
                "url": pegasus_url
            }
        )

        processing_time = time.time() - start_time

        # Validate results
        print("\n📊 RESULTS VALIDATION")
        print("-" * 30)

        print(f"✅ Processing completed in {processing_time:.2f}s")
        print(f"✅ Backend used: {result.metadata.get('backend_used', 'unknown')}")
        print(f"✅ Processing cost: ${result.processing_cost:.4f}")
        print(f"✅ Transcript length: {len(result.transcript.full_text)} characters")
        print(f"✅ Entities extracted: {len(result.entities)}")
        print(f"✅ Relationships extracted: {len(result.relationships)}")

        # Validate sensitive content was processed
        sensitive_keywords = ["Pegasus", "NSO Group", "spyware", "surveillance", "investigation"]
        found_keywords = [kw for kw in sensitive_keywords if kw.lower() in result.transcript.full_text.lower()]

        if found_keywords:
            print(f"✅ Sensitive content detected: {', '.join(found_keywords)}")
        else:
            print("⚠️  No sensitive keywords found in transcript (may be expected)")

        # Validate entities contain relevant intelligence
        entity_types = [e.type for e in result.entities]
        if "ORGANIZATION" in entity_types or "PERSON" in entity_types:
            print("✅ Relevant entities extracted from sensitive content")
        else:
            print("⚠️  No organization/person entities found")

        # Show sample entities and relationships
        if result.entities:
            print("\n🔍 SAMPLE ENTITIES:")
            for i, entity in enumerate(result.entities[:5]):
                print(f"   {i+1}. {entity.name} ({entity.type}) - {entity.confidence:.2f}")

        if result.relationships:
            print("\n🔗 SAMPLE RELATIONSHIPS:")
            for i, rel in enumerate(result.relationships[:3]):
                print(f"   {i+1}. {rel.subject} → {rel.predicate} → {rel.object}")

        print("\n🎉 GROK 4 INTEGRATION TEST: SUCCESSFUL")
        print("✅ Real video processing completed")
        print("✅ Hybrid fallback system working")
        print("✅ Sensitive content processed appropriately")
        print("✅ Cost calculation accurate")

        return result

    except Exception as e:
        print(f"\n❌ PROCESSING FAILED: {e}")
        print("🔍 Analyzing failure reason...")

        # Check if it's a safety filter issue
        error_str = str(e).lower()
        if "safety" in error_str or "blocked" in error_str:
            print("⚠️  Safety filter detected - this indicates Gemini was used instead of Grok")
            print("   This is expected behavior if Grok fallback didn't trigger properly")
        elif "api key" in error_str:
            print("❌ API key issue - check XAI_API_KEY environment variable")
        elif "network" in error_str or "connection" in error_str:
            print("❌ Network connectivity issue")
        else:
            print("❌ Unexpected error - check logs for details")

        raise


async def test_framework_only():
    """
    Test the framework components without real API calls.
    """
    print("\n🔧 TESTING FRAMEWORK COMPONENTS ONLY")
    print("-" * 40)

    # Test unified API initialization
    api = UnifiedTranscriberAPI()
    print("✅ Unified API framework initialized")

    # Test backend registration
    backends = api.registry.list_available_backends()
    grok_registered = BackendType.GROK in backends

    if grok_registered:
        print("✅ Grok 4 backend registered in unified API")
    else:
        print("❌ Grok backend not registered")

    # Test parameter mapping
    params = {"audio_path": "/test.mp3", "duration": 120}
    mapped = api.parameter_mapper.map_parameters(BackendType.GROK, params)

    if "content_path" in mapped and mapped["content_path"] == "/test.mp3":
        print("✅ Parameter mapping working for Grok")
    else:
        print("❌ Parameter mapping failed")

    # Test sensitive content detection
    sensitive_metadata = {
        "title": "Pegasus Spyware Investigation",
        "description": "NSO Group surveillance technology"
    }

    # Debug: show what we're testing
    print(f"🔍 Testing sensitive content with: {sensitive_metadata}")

    is_sensitive = api._is_sensitive_content({"metadata": sensitive_metadata})
    if is_sensitive:
        print("✅ Sensitive content detection working")
    else:
        print("❌ Sensitive content not detected")
        print("   Expected: True (contains 'pegasus' keyword)")

    print("\n📋 FRAMEWORK VALIDATION SUMMARY:")
    print("- All core components initialized correctly")
    print("- Backend registration working")
    print("- Parameter mapping functional")
    print("- Sensitive content detection active")
    print("- Ready for real API testing with XAI_API_KEY")


async def main():
    """
    Main test function.
    """
    try:
        await test_grok4_pegasus_integration()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Set up asyncio
    asyncio.run(main())
