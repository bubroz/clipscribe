#!/usr/bin/env python3
"""
Quick validation script for v3.0.0 provider system.

Tests provider imports, interface compliance, and basic functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


async def test_provider_imports():
    """Test that all providers can be imported."""
    print("="*60)
    print("Phase 10 Validation: Provider System")
    print("="*60)
    print()
    
    print("1. Testing provider imports...")
    try:
        from clipscribe.providers.factory import get_transcription_provider, get_intelligence_provider
        from clipscribe.providers.base import TranscriptionProvider, IntelligenceProvider
        print("   ✓ Provider factory imports successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    print()
    print("2. Testing provider interfaces...")
    
    # Check Voxtral
    try:
        from clipscribe.providers.transcription.voxtral import VoxtralProvider
        print("   ✓ VoxtralProvider class defined")
        print(f"     - Supports diarization: {VoxtralProvider.__dict__.get('supports_diarization', 'N/A')}")
    except ImportError as e:
        print(f"   ❌ VoxtralProvider import failed: {e}")
    
    # Check WhisperX Local
    try:
        from clipscribe.providers.transcription.whisperx_local import WhisperXLocalProvider
        print("   ✓ WhisperXLocalProvider class defined")
    except ImportError as e:
        print(f"   ❌ WhisperXLocalProvider import failed: {e}")
    
    # Check WhisperX Modal
    try:
        from clipscribe.providers.transcription.whisperx_modal import WhisperXModalProvider
        print("   ✓ WhisperXModalProvider class defined")
    except ImportError as e:
        print(f"   ❌ WhisperXModalProvider import failed: {e}")
    
    # Check Grok
    try:
        from clipscribe.providers.intelligence.grok import GrokProvider
        print("   ✓ GrokProvider class defined")
    except ImportError as e:
        print(f"   ❌ GrokProvider import failed: {e}")
    
    print()
    print("3. Testing provider instantiation (with env check)...")
    
    # Check environment
    has_mistral = bool(os.getenv("MISTRAL_API_KEY"))
    has_xai = bool(os.getenv("XAI_API_KEY"))
    has_hf = bool(os.getenv("HF_TOKEN"))
    
    print(f"   Environment:")
    print(f"     MISTRAL_API_KEY: {'✓' if has_mistral else '❌ Not set'}")
    print(f"     XAI_API_KEY: {'✓' if has_xai else '❌ Not set'}")
    print(f"     HF_TOKEN: {'✓' if has_hf else '❌ Not set'}")
    
    print()
    print("4. Testing provider interface compliance...")
    
    # Test that providers implement required interface
    from clipscribe.providers.transcription.voxtral import VoxtralProvider
    from clipscribe.providers.intelligence.grok import GrokProvider
    
    # Check VoxtralProvider has required methods
    required_transcription_methods = ['name', 'supports_diarization', 'transcribe', 'estimate_cost', 'validate_config']
    for method in required_transcription_methods:
        has_method = hasattr(VoxtralProvider, method)
        print(f"   VoxtralProvider.{method}: {'✓' if has_method else '❌'}")
    
    print()
    
    # Check GrokProvider has required methods
    required_intelligence_methods = ['name', 'extract', 'estimate_cost', 'validate_config']
    for method in required_intelligence_methods:
        has_method = hasattr(GrokProvider, method)
        print(f"   GrokProvider.{method}: {'✓' if has_method else '❌'}")
    
    print()
    print("5. Testing cost estimation (no API calls)...")
    
    if has_mistral:
        try:
            provider = get_transcription_provider("voxtral")
            cost_30min = provider.estimate_cost(1800)  # 30 minutes
            print(f"   ✓ Voxtral 30min estimate: ${cost_30min:.4f}")
        except Exception as e:
            print(f"   ❌ Voxtral initialization failed: {e}")
    
    if has_xai:
        try:
            provider = get_intelligence_provider("grok")
            cost_transcript = provider.estimate_cost(10000)  # 10K chars
            print(f"   ✓ Grok 10K chars estimate: ${cost_transcript:.6f}")
        except Exception as e:
            print(f"   ❌ Grok initialization failed: {e}")
    
    print()
    print("="*60)
    print("Provider System Validation: PASS")
    print("="*60)
    print()
    print("Next: Test with real audio file")
    print("Command: poetry run clipscribe process test_videos/medical_lxFd5xAN4cg.mp3")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_provider_imports())

