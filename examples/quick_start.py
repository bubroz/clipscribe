#!/usr/bin/env python3
"""ClipScribe v3.0.0 Quick Start - File-first processing with providers."""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import ClipScribe providers
from clipscribe.providers.factory import get_transcription_provider, get_intelligence_provider


async def main():
    """Simple example of processing an audio file with ClipScribe v3.0.0."""
    
    print("🎯 ClipScribe v3.0.0 Quick Start")
    print("=" * 60)
    print()
    
    # Audio file path
    audio_file = "path/to/your/audio.mp3"
    
    # Choose providers
    # Options: "voxtral" (cheap), "whisperx-local" (FREE), "whisperx-modal" (cloud GPU)
    transcription_provider = "whisperx-local"  # FREE!
    intelligence_provider = "grok"
    
    print(f"📁 File: {audio_file}")
    print(f"🔧 Transcription: {transcription_provider}")
    print(f"🧠 Intelligence: {intelligence_provider}")
    print()
    
    try:
        # Get providers
        print("Loading providers...")
        transcriber = get_transcription_provider(transcription_provider)
        extractor = get_intelligence_provider(intelligence_provider)
        
        # Transcribe
        print(f"\n📝 Transcribing with {transcription_provider}...")
        transcript = await transcriber.transcribe(audio_file, diarize=True)
        
        print(f"✓ Transcribed: {transcript.language}")
        print(f"  Duration: {transcript.duration/60:.1f} minutes")
        print(f"  Speakers: {transcript.speakers}")
        print(f"  Cost: ${transcript.cost:.4f}")
        
        # Extract intelligence
        print(f"\n🧠 Extracting intelligence with {intelligence_provider}...")
        intelligence = await extractor.extract(transcript)
        
        print(f"✓ Extracted:")
        print(f"  Entities: {len(intelligence.entities)}")
        print(f"  Relationships: {len(intelligence.relationships)}")
        print(f"  Topics: {len(intelligence.topics)}")
        print(f"  Cost: ${intelligence.cost:.4f}")
        
        # Total cost
        total_cost = transcript.cost + intelligence.cost
        print(f"\n💰 Total cost: ${total_cost:.4f}")
        
        # Sample output
        if intelligence.entities:
            print(f"\n📊 Sample Entities:")
            for entity in intelligence.entities[:3]:
                print(f"  • {entity['name']} ({entity['type']})")
        
        if intelligence.cache_stats.get('cached_tokens', 0) > 0:
            savings = intelligence.cache_stats.get('cache_savings', 0)
            print(f"\n💾 Cache savings: ${savings:.4f}")
        
        print("\n✅ Success!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  • Run: poetry run clipscribe utils check-auth")
        print("  • See: docs/TROUBLESHOOTING.md")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  ClipScribe v3.0.0 - File-First Processing")
    print("  Provider options: voxtral, whisperx-local, whisperx-modal")
    print("="*60 + "\n")
    
    asyncio.run(main())
