#!/usr/bin/env python3
"""
Test Voxtral EXACTLY as shown in official documentation.
Based on: https://docs.mistral.ai/capabilities/audio/#transcription-with-timestamps
"""

import os
import asyncio
from mistralai import Mistral
from pathlib import Path
import json

async def test_official_method():
    """Test using the official Mistral SDK exactly as documented."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    # Initialize the Mistral client (official SDK)
    client = Mistral(api_key=api_key)
    
    # Test with our 5-minute speech file
    test_audio = Path("test_speech_5min.mp3")
    if not test_audio.exists():
        print(f"Test audio not found: {test_audio}")
        return
    
    print(f"Testing with: {test_audio} ({test_audio.stat().st_size / 1024:.1f} KB)")
    print("\nUsing OFFICIAL Mistral SDK method from docs...")
    
    try:
        # Method 1: Upload file and use signed URL (as shown in docs)
        print("\n1. Uploading file...")
        with open(test_audio, "rb") as f:
            uploaded_audio = client.files.upload(
                file={
                    "content": f,
                    "file_name": f.name
                },
                purpose="audio"
            )
        print(f"   File uploaded: {uploaded_audio.id}")
        
        print("\n2. Getting signed URL...")
        signed_url = client.files.get_signed_url(file_id=uploaded_audio.id)
        print(f"   Got signed URL")
        
        print("\n3. Transcribing with official SDK...")
        # EXACTLY as shown in the documentation
        transcription = client.audio.transcriptions.create(
            model="voxtral-mini-2507",
            file_url=signed_url.url,
            response_format="verbose_json"  # This should give us segments
        )
        
        print("\n4. Analyzing response...")
        
        # The response should be a dict with these fields
        if isinstance(transcription, dict):
            result = transcription
        else:
            # If it's an object, convert to dict
            result = transcription.model_dump() if hasattr(transcription, 'model_dump') else vars(transcription)
        
        print(f"   Response type: {type(transcription)}")
        print(f"   Response keys: {list(result.keys())}")
        
        # Check what we got
        if "text" in result:
            print(f"   ✅ Text: {len(result['text'])} chars")
            print(f"      Sample: {result['text'][:100]}...")
        
        if "language" in result:
            print(f"   ✅ Language: {result['language']}")
        
        if "segments" in result:
            segments = result["segments"]
            print(f"   {'✅' if segments else '❌'} Segments: {len(segments)}")
            if segments:
                print(f"\n   First 3 segments:")
                for i, seg in enumerate(segments[:3]):
                    print(f"      [{i}] {seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s")
                    print(f"          Text: {seg.get('text', '')[:80]}...")
        else:
            print("   ❌ No 'segments' field in response!")
        
        if "usage" in result:
            usage = result["usage"]
            print(f"\n   Usage:")
            print(f"      Audio seconds: {usage.get('prompt_audio_seconds', 0)}")
            print(f"      Total tokens: {usage.get('total_tokens', 0)}")
        
        # Save full response for inspection
        with open("voxtral_response.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n   Full response saved to: voxtral_response.json")
        
        # Clean up
        print("\n5. Cleaning up...")
        client.files.delete(file_id=uploaded_audio.id)
        print("   File deleted")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_alternative_method():
    """Test with base64 encoding as shown in docs."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    client = Mistral(api_key=api_key)
    
    # Create a small test file
    test_audio = Path("test_audio.mp3")
    if not test_audio.exists():
        print("Creating small test audio...")
        import subprocess
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "sine=frequency=1000:duration=10",
            "-ar", "44100", "test_audio.mp3", "-y"
        ], capture_output=True)
    
    print(f"\nTesting with base64 method: {test_audio} ({test_audio.stat().st_size / 1024:.1f} KB)")
    
    try:
        import base64
        
        # Encode audio in base64 (as shown in docs)
        with open(test_audio, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        print("Transcribing with base64 encoded audio...")
        
        # Try the transcription
        transcription = client.audio.transcriptions.create(
            model="voxtral-mini-2507",
            audio=audio_base64,  # Using base64 instead of file_url
            response_format="verbose_json"
        )
        
        # Analyze response
        if isinstance(transcription, dict):
            result = transcription
        else:
            result = transcription.model_dump() if hasattr(transcription, 'model_dump') else vars(transcription)
        
        print(f"Response keys: {list(result.keys())}")
        print(f"Segments: {len(result.get('segments', []))}")
        
    except Exception as e:
        print(f"Error with base64 method: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING VOXTRAL EXACTLY AS DOCUMENTED")
    print("=" * 60)
    
    asyncio.run(test_official_method())
    
    print("\n" + "=" * 60)
    print("TESTING ALTERNATIVE BASE64 METHOD")
    print("=" * 60)
    
    asyncio.run(test_alternative_method())
