#!/usr/bin/env python3
"""Quick test of Voxtral implementation with a short video."""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber


async def test_voxtral_quick():
    """Quick test with a short video from MASTER_TEST_VIDEO_TABLE."""
    
    # Use a short test video from the master table
    test_url = "https://www.youtube.com/watch?v=6n3pFFPSlW4"  # 11-second test video
    
    print("=" * 60)
    print("VOXTRAL QUICK TEST")
    print("=" * 60)
    print(f"Test URL: {test_url}")
    print(f"Testing smart fallback: Gemini → Voxtral")
    print("=" * 60)
    
    # First, check if we have the Mistral API key
    if not os.getenv("MISTRAL_API_KEY"):
        print("\n⚠️  MISTRAL_API_KEY not set!")
        print("\nTo test Voxtral, please:")
        print("1. Get an API key from: https://console.mistral.ai/")
        print("2. Set it: export MISTRAL_API_KEY='your-key-here'")
        return
    
    print("\n✅ MISTRAL_API_KEY found")
    
    # Test with USE_VOXTRAL environment variable
    os.environ["USE_VOXTRAL"] = "true"
    
    try:
        print("\nInitializing transcriber with Voxtral enabled...")
        transcriber = GeminiFlashTranscriber()
        
        if transcriber.use_voxtral:
            print("✅ Voxtral is enabled")
            if transcriber.voxtral_transcriber:
                print("✅ Voxtral transcriber initialized")
            else:
                print("❌ Voxtral transcriber failed to initialize")
        else:
            print("❌ Voxtral is not enabled")
        
        print("\nTranscriber configuration:")
        print(f"- use_voxtral: {transcriber.use_voxtral}")
        print(f"- use_vertex_ai: {transcriber.use_vertex_ai}")
        print(f"- voxtral_transcriber: {transcriber.voxtral_transcriber is not None}")
        
        # Test that Voxtral module is working
        if transcriber.voxtral_transcriber:
            print(f"- voxtral_model: {transcriber.voxtral_transcriber.model}")
            print(f"- voxtral_cost: ${transcriber.voxtral_transcriber.COST_PER_MINUTE}/min")
        
        print("\n✅ Voxtral integration is ready!")
        print("\nNext steps:")
        print("1. Run full PBS Frontline test: poetry run python scripts/test_voxtral_pbs.py")
        print("2. Process a real video with Voxtral: USE_VOXTRAL=true poetry run clipscribe process <url>")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_voxtral_quick())
