#!/usr/bin/env python3
"""
Test with Full Transcript Analysis

Tests entity extraction using the FULL transcript, not just first 24k chars.

Usage:
    poetry run python scripts/test_full_transcript.py
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_with_full_transcript():
    """Test with proper full transcript analysis."""
    
    # Use a medium-length video for testing
    test_url = "https://www.youtube.com/watch?v=A-bdxIi7v04"  # PBS News 26 min
    
    print("=" * 80)
    print("FULL TRANSCRIPT ANALYSIS TEST")
    print("=" * 80)
    print(f"Test URL: {test_url}")
    print()
    
    from src.clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
    from src.clipscribe.retrievers.transcriber import GeminiFlashTranscriber
    import google.generativeai as genai
    
    # Download video once
    print("📥 Downloading video...")
    client = EnhancedUniversalVideoClient()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path, metadata = await client.download_audio(test_url, output_dir=tmpdir)
        
        duration = int(getattr(metadata, "duration", 0) or 0)
        title = getattr(metadata, "title", "Unknown")
        
        print(f"✅ Downloaded: {title}")
        print(f"   Duration: {duration}s ({duration/60:.1f} minutes)")
        
        results = {}
        
        for use_pro in [False, True]:
            model = "pro" if use_pro else "flash"
            print(f"\n{'='*40}")
            print(f"Testing {model.upper()} with FULL transcript")
            print('='*40)
            
            # Get transcript
            print(f"\n1️⃣ Getting transcript with {model.upper()}...")
            transcriber = GeminiFlashTranscriber(use_pro=use_pro)
            
            # First, just get the transcript
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model_name = "gemini-2.5-pro" if use_pro else "gemini-2.5-flash"
            
            with open(audio_path, "rb") as f:
                audio_data = f.read()
            
            upload_result = genai.upload_file(
                path=audio_path,
                mime_type="audio/mpeg",
                display_name=f"audio_{model}.mp3"
            )
            
            gemini_model = genai.GenerativeModel(model_name)
            
            # Get full transcript
            transcript_response = await gemini_model.generate_content_async(
                [upload_result, "Transcribe this audio completely. Return only the transcript text."]
            )
            
            transcript_text = transcript_response.text
            print(f"   Transcript length: {len(transcript_text)} characters")
            
            # Analyze FULL transcript
            print(f"\n2️⃣ Analyzing FULL transcript ({len(transcript_text)} chars)...")
            
            analysis_prompt = f"""
            Analyze this COMPLETE transcript and extract:
            1. ALL entities (people, places, organizations, concepts)
            2. ALL relationships between entities
            3. Key points and topics
            
            Be EXHAUSTIVE - extract EVERYTHING relevant.
            
            FULL TRANSCRIPT:
            {transcript_text}
            
            Return as JSON with: entities, relationships, key_points, topics
            """
            
            # Use larger token limit for Pro
            max_tokens = 8192 if use_pro else 4096
            
            analysis_response = await gemini_model.generate_content_async(
                [analysis_prompt],
                generation_config={
                    "response_mime_type": "application/json",
                    "max_output_tokens": max_tokens,
                    "temperature": 0.1  # Lower temperature for consistency
                }
            )
            
            try:
                analysis_data = json.loads(analysis_response.text)
            except:
                print(f"   ❌ Failed to parse JSON response")
                continue
            
            entities = analysis_data.get("entities", [])
            relationships = analysis_data.get("relationships", [])
            
            print(f"\n📊 Results with FULL transcript:")
            print(f"   Entities found: {len(entities)}")
            print(f"   Relationships found: {len(relationships)}")
            
            # Sample entities
            if entities and isinstance(entities, list):
                print("\n   Sample entities:")
                for i, entity in enumerate(entities[:5]):
                    if isinstance(entity, dict):
                        name = entity.get("name", entity) if isinstance(entity, dict) else str(entity)
                        print(f"     {i+1}. {name}")
                    else:
                        print(f"     {i+1}. {entity}")
            
            results[model] = {
                "transcript_length": len(transcript_text),
                "entities": len(entities),
                "relationships": len(relationships)
            }
            
            # Clean up uploaded file
            upload_result.delete()
    
    # Compare results
    print("\n" + "="*80)
    print("COMPARISON: FULL TRANSCRIPT ANALYSIS")
    print("="*80)
    
    if "flash" in results and "pro" in results:
        flash = results["flash"]
        pro = results["pro"]
        
        print(f"\nFlash (FULL {flash['transcript_length']} chars):")
        print(f"  Entities: {flash['entities']}")
        print(f"  Relationships: {flash['relationships']}")
        
        print(f"\nPro (FULL {pro['transcript_length']} chars):")
        print(f"  Entities: {pro['entities']}")
        print(f"  Relationships: {pro['relationships']}")
        
        print(f"\nDifference:")
        entity_diff = pro['entities'] - flash['entities']
        rel_diff = pro['relationships'] - flash['relationships']
        
        print(f"  Entities: {entity_diff:+d} ({entity_diff/max(flash['entities'],1)*100:+.1f}%)")
        print(f"  Relationships: {rel_diff:+d} ({rel_diff/max(flash['relationships'],1)*100:+.1f}%)")
        
        print(f"\n📊 Analysis:")
        if entity_diff > 0 and rel_diff > 0:
            print("  ✅ With FULL transcript, Pro extracts more entities/relationships")
        elif abs(entity_diff) < 5 and abs(rel_diff) < 5:
            print("  🤝 Similar performance when analyzing full transcript")
        else:
            print("  ⚠️ Significant differences remain even with full transcript")


async def main():
    """Main entry point."""
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not set")
        sys.exit(1)
    
    await test_with_full_transcript()


if __name__ == "__main__":
    asyncio.run(main())
