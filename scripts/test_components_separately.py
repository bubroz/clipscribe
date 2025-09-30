#!/usr/bin/env python3
"""
Test individual components separately to isolate issues.
Run each component test independently to avoid timeouts.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clipscribe.retrievers.voxtral_transcriber import VoxtralTranscriber
from src.clipscribe.processors.hybrid_processor import HybridProcessor
from src.clipscribe.core_data import CoreData


async def test_voxtral_only():
    """Test only Voxtral transcription (no Grok)."""
    print("=" * 60)
    print("TESTING VOXTRAL TRANSCRIPTION ONLY")
    print("=" * 60)
    
    # This should be fast - just transcription
    transcriber = VoxtralTranscriber(model="voxtral-mini-2507")
    
    # Use a small test audio file
    test_audio = "test_audio.mp3"  # You'd need to create this
    if not Path(test_audio).exists():
        print("❌ No test audio file found. Create test_audio.mp3 first.")
        return False
    
    try:
        result = await transcriber.transcribe_audio(test_audio)
        print(f"✅ Transcription completed: {len(result['transcript'])} characters")
        print(f"✅ Cost: ${result.get('processing_cost', 0):.3f}")
        return True
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return False


async def test_grok_only():
    """Test only Grok extraction (with mock transcript)."""
    print("=" * 60)
    print("TESTING GROK EXTRACTION ONLY")
    print("=" * 60)
    
    # Mock transcript for testing
    mock_transcript = "This is a test transcript about Tier 1 and Tier 2 operations."
    
    try:
        processor = HybridProcessor(
            voxtral_model="voxtral-mini-2507",
            grok_model="grok-4-0709"
        )
        
        # Test just the Grok extraction part
        result = await processor.extract_entities_grok(mock_transcript)
        print(f"✅ Grok extraction completed: {len(result.get('entities', []))} entities")
        return True
    except Exception as e:
        print(f"❌ Grok extraction failed: {e}")
        return False


async def test_core_data_only():
    """Test only CoreData model validation."""
    print("=" * 60)
    print("TESTING CORE DATA MODEL ONLY")
    print("=" * 60)
    
    try:
        # Create minimal test data
        core_data = CoreData(
            video_id="test_123",
            title="Test Video",
            transcript="Test transcript content",
            entities=[],
            relationships=[],
            metadata={"video_id": "test_123", "title": "Test Video"}
        )
        
        # Validate
        core_data.validate()
        print("✅ CoreData validation passed")
        
        # Test derived outputs
        facts = core_data.generate_facts()
        print(f"✅ Generated {len(facts)} facts")
        
        return True
    except Exception as e:
        print(f"❌ CoreData test failed: {e}")
        return False


def main():
    """Run individual component tests."""
    print("Choose a component to test:")
    print("1. Voxtral transcription only")
    print("2. Grok extraction only") 
    print("3. CoreData model only")
    print("4. All components (sequential)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(test_voxtral_only())
    elif choice == "2":
        asyncio.run(test_grok_only())
    elif choice == "3":
        asyncio.run(test_core_data_only())
    elif choice == "4":
        print("Running all components sequentially...")
        asyncio.run(test_voxtral_only())
        asyncio.run(test_grok_only())
        asyncio.run(test_core_data_only())
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
