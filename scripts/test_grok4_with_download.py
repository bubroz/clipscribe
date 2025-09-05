#!/usr/bin/env python3
"""
Test Grok 4 Integration with proper video downloading.

This test properly downloads videos BEFORE attempting transcription,
which is required for Gemini but optional for Grok.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.api.unified_transcriber import UnifiedTranscriberAPI, BackendType
from src.clipscribe.retrievers.universal_video_client import UniversalVideoClient
from src.clipscribe.config.settings import Settings


async def test_with_downloaded_video():
    """Test Grok with a properly downloaded video."""
    print("🚀 GROK 4 VALIDATION WITH PROPER DOWNLOAD")
    print("=" * 80)
    
    # Check for API key
    settings = Settings()
    if not settings.xai_api_key:
        print("❌ XAI_API_KEY not found in environment!")
        print("Please set it in .env.production or as environment variable")
        return False
    
    print(f"✅ XAI API Key: {settings.xai_api_key[:3]}***{settings.xai_api_key[-4:]}")
    print()
    
    # Test with a short video to save time
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - 19 seconds
    
    print("📥 STEP 1: DOWNLOAD VIDEO")
    print("-" * 40)
    
    # Download the video first
    downloader = UniversalVideoClient()
    try:
        print(f"Downloading: {test_url}")
        audio_path, metadata = await downloader.download_audio(test_url)
        print(f"✅ Downloaded to: {audio_path}")
        print(f"✅ Duration: {metadata.duration} seconds")
        print(f"✅ Title: {metadata.title}")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False
    
    print()
    print("🤖 STEP 2: TEST GROK TRANSCRIPTION")
    print("-" * 40)
    
    # Initialize the unified API
    api = UnifiedTranscriberAPI()
    
    # Prepare metadata dict for API
    metadata_dict = {
        "title": metadata.title,
        "description": metadata.description,
        "channel": metadata.channel,
        "url": metadata.url,
        "duration": metadata.duration
    }
    
    try:
        # Test Grok directly (should work with sensitive content)
        print("Testing Grok 4 transcription...")
        start_time = time.time()
        
        # Force Grok backend
        result = await api.transcribe(
            audio_path=str(audio_path),  # Use downloaded file path
            metadata=metadata_dict,
            backend_preference=[BackendType.GROK]  # Force Grok
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ Transcription successful!")
        print(f"⏱️  Time: {elapsed:.1f}s")
        print(f"💰 Cost: ${result.processing_cost:.4f}")
        print(f"📝 Transcript length: {len(result.transcript)} chars")
        print(f"🎯 Entities found: {len(result.entities)}")
        print(f"🔗 Relationships found: {len(result.relationships)}")
        
        # Show first few entities
        if result.entities:
            print("\nSample entities:")
            for entity in result.entities[:3]:
                print(f"  - {entity.get('name', 'Unknown')} ({entity.get('type', 'Unknown')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up downloaded file
        if audio_path and Path(audio_path).exists():
            print(f"\n🧹 Cleaning up: {audio_path}")
            Path(audio_path).unlink()


async def test_gemini_with_download():
    """Test Gemini with a properly downloaded video."""
    print("\n" + "=" * 80)
    print("🚀 GEMINI VALIDATION WITH PROPER DOWNLOAD")
    print("=" * 80)
    
    # Test with a short video
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - 19 seconds
    
    print("📥 STEP 1: DOWNLOAD VIDEO")
    print("-" * 40)
    
    # Download the video first
    downloader = UniversalVideoClient()
    try:
        print(f"Downloading: {test_url}")
        audio_path, metadata = await downloader.download_audio(test_url)
        print(f"✅ Downloaded to: {audio_path}")
        print(f"✅ Duration: {metadata.duration} seconds")
        print(f"✅ Title: {metadata.title}")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False
    
    print()
    print("🤖 STEP 2: TEST GEMINI TRANSCRIPTION")
    print("-" * 40)
    
    # Initialize the unified API
    api = UnifiedTranscriberAPI()
    
    # Prepare metadata dict
    metadata_dict = {
        "title": metadata.title,
        "description": metadata.description,
        "channel": metadata.channel,
        "url": metadata.url,
        "duration": metadata.duration
    }
    
    try:
        # Test Gemini (default)
        print("Testing Gemini Flash transcription...")
        start_time = time.time()
        
        result = await api.transcribe(
            audio_path=str(audio_path),  # Use downloaded file path
            metadata=metadata_dict,
            backend_preference=[BackendType.GEMINI]  # Force Gemini
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ Transcription successful!")
        print(f"⏱️  Time: {elapsed:.1f}s")
        print(f"💰 Cost: ${result.processing_cost:.4f}")
        print(f"📝 Transcript length: {len(result.transcript)} chars")
        print(f"🎯 Entities found: {len(result.entities)}")
        print(f"🔗 Relationships found: {len(result.relationships)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        if audio_path and Path(audio_path).exists():
            print(f"\n🧹 Cleaning up: {audio_path}")
            Path(audio_path).unlink()


async def main():
    """Run all tests."""
    print("🎯 COMPREHENSIVE API VALIDATION WITH PROPER DOWNLOADS")
    print("Testing both Grok and Gemini with downloaded files")
    print("=" * 80)
    print()
    
    # Test Grok
    grok_success = await test_with_downloaded_video()
    
    # Test Gemini
    gemini_success = await test_gemini_with_download()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS:")
    print("=" * 80)
    print(f"Grok 4:  {'✅ PASSED' if grok_success else '❌ FAILED'}")
    print(f"Gemini:  {'✅ PASSED' if gemini_success else '❌ FAILED'}")
    
    if grok_success and gemini_success:
        print("\n🎉 All tests passed! The API abstraction layer is working correctly.")
    elif grok_success and not gemini_success:
        print("\n⚠️  Grok works but Gemini failed. Check Gemini API key/quota.")
    elif not grok_success and gemini_success:
        print("\n⚠️  Gemini works but Grok failed. Check XAI_API_KEY.")
    else:
        print("\n❌ Both backends failed. Check API keys and network.")
    
    return grok_success and gemini_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
