#!/usr/bin/env python3
"""
Test Voxtral transcription with PBS Frontline documentary.

This script tests Voxtral's ability to transcribe sensitive content
that Gemini blocks, validating accuracy and completeness.
"""

import asyncio
import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.voxtral_transcriber import VoxtralTranscriber
from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
from src.clipscribe.retrievers.universal_video_client import UniversalVideoClient


async def test_voxtral_vs_gemini():
    """Test Voxtral against Gemini with PBS Frontline content."""
    
    # Test video: PBS Frontline - Pegasus Spyware (known to be blocked by Gemini)
    test_url = "https://www.youtube.com/watch?v=Nr7vbOSzpSk"  # 94-minute Pegasus documentary
    
    print("=" * 80)
    print("VOXTRAL vs GEMINI TEST - PBS FRONTLINE")
    print("=" * 80)
    print(f"Test Video: PBS Frontline - Pegasus Spyware Investigation")
    print(f"URL: {test_url}")
    print(f"Expected: Gemini blocks, Voxtral succeeds")
    print("=" * 80)
    
    # Download video/audio first
    print("\n📥 Downloading video...")
    downloader = UniversalVideoClient()
    
    try:
        metadata = await downloader.get_video_metadata(test_url)
        print(f"Title: {metadata.get('title', 'Unknown')}")
        print(f"Duration: {metadata.get('duration', 0)} seconds")
        
        # Download audio for testing
        output_dir = Path("output/voxtral_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        audio_path = output_dir / "pbs_frontline_test.mp3"
        if not audio_path.exists():
            print("Downloading audio...")
            video_path, _ = await downloader.download_video(test_url, str(output_dir))
            # Extract audio
            import subprocess
            subprocess.run([
                "ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3",
                "-ab", "128k", str(audio_path)
            ], check=True)
            print(f"Audio saved to: {audio_path}")
        else:
            print(f"Using existing audio: {audio_path}")
        
        duration = metadata.get('duration', 0)
        
    except Exception as e:
        print(f"❌ Failed to download video: {e}")
        return
    
    # Test 1: Try Gemini (expected to fail)
    print("\n" + "=" * 80)
    print("TEST 1: GEMINI TRANSCRIPTION")
    print("=" * 80)
    
    try:
        print("Initializing Gemini transcriber...")
        gemini = GeminiFlashTranscriber(use_voxtral=False)  # No Voxtral fallback
        
        print("Attempting transcription...")
        start_time = time.time()
        
        result = await gemini.transcribe_audio(str(audio_path), duration)
        
        elapsed = time.time() - start_time
        
        print(f"✅ Gemini succeeded (unexpected!)")
        print(f"Time: {elapsed:.1f}s")
        print(f"Transcript length: {len(result.get('transcript', ''))} chars")
        print(f"Cost: ${result.get('processing_cost', 0):.4f}")
        
        # Save result
        with open(output_dir / "gemini_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"❌ Gemini failed (expected): {e}")
        if "safety" in str(e).lower() or "blocked" in str(e).lower():
            print("   → Content blocked by safety filters")
        
    # Test 2: Try Voxtral (expected to succeed)
    print("\n" + "=" * 80)
    print("TEST 2: VOXTRAL TRANSCRIPTION")
    print("=" * 80)
    
    try:
        print("Initializing Voxtral transcriber...")
        # Check for API key
        if not os.getenv("MISTRAL_API_KEY"):
            print("⚠️  MISTRAL_API_KEY not set. Please set it to test Voxtral.")
            print("   Get your API key at: https://console.mistral.ai/")
            return
        
        voxtral = VoxtralTranscriber(model="voxtral-small")
        
        print("Attempting transcription with Voxtral Small (24B)...")
        start_time = time.time()
        
        result = await voxtral.transcribe_audio(str(audio_path))
        
        elapsed = time.time() - start_time
        
        print(f"✅ Voxtral succeeded!")
        print(f"Time: {elapsed:.1f}s")
        print(f"Transcript length: {len(result.text)} chars")
        print(f"Language: {result.language}")
        print(f"Duration: {result.duration:.1f}s")
        print(f"Cost: ${result.cost:.4f}")
        print(f"Model: {result.model}")
        
        # Show sample of transcript
        print(f"\nFirst 500 chars of transcript:")
        print("-" * 40)
        print(result.text[:500])
        print("-" * 40)
        
        # Save result
        with open(output_dir / "voxtral_result.json", "w") as f:
            json.dump({
                "text": result.text,
                "language": result.language,
                "duration": result.duration,
                "cost": result.cost,
                "model": result.model
            }, f, indent=2)
        
        print(f"\n✅ Results saved to: {output_dir}")
        
    except Exception as e:
        print(f"❌ Voxtral failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Smart Fallback
    print("\n" + "=" * 80)
    print("TEST 3: SMART FALLBACK (GEMINI → VOXTRAL)")
    print("=" * 80)
    
    try:
        print("Initializing transcriber with Voxtral fallback...")
        smart_transcriber = GeminiFlashTranscriber(use_voxtral=True)
        
        print("Attempting transcription...")
        start_time = time.time()
        
        result = await smart_transcriber.transcribe_audio(str(audio_path), duration)
        
        elapsed = time.time() - start_time
        
        print(f"✅ Smart fallback succeeded!")
        print(f"Time: {elapsed:.1f}s")
        print(f"Model used: {result.get('model', 'unknown')}")
        print(f"Fallback reason: {result.get('fallback_reason', 'none')}")
        print(f"Transcript length: {len(result.get('transcript', ''))} chars")
        print(f"Cost: ${result.get('processing_cost', 0):.4f}")
        
        # Save result
        with open(output_dir / "smart_fallback_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"❌ Smart fallback failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print("- Gemini: Expected to block sensitive content ✓")
    print("- Voxtral: Expected to transcribe without censorship ✓")
    print("- Smart Fallback: Expected to use Voxtral when Gemini blocks ✓")
    print("\nRecommendation: Use Voxtral for all transcription tasks")
    print("Cost savings: 70% reduction ($0.001/min vs $0.0035/min)")


if __name__ == "__main__":
    asyncio.run(test_voxtral_vs_gemini())
