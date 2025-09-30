#!/usr/bin/env python3
"""
Test Voxtral transcription API directly to verify segment timestamps.
Based on official Mistral documentation.
"""

import os
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_voxtral_transcription():
    """Test Voxtral transcription endpoint per official docs."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    # Find a real audio file to test with
    test_audio = Path("test_speech_5min.mp3")
    if not test_audio.exists():
        test_audio = Path("test_speech.mp3")
        if not test_audio.exists():
            test_audio = Path("test_rick.mp3")
            if not test_audio.exists():
                for path in Path(".").glob("*.mp3"):
                    if path.stat().st_size > 100000:  # At least 100KB
                        test_audio = path
                        break
                else:
                    print("No suitable test audio file found")
                    return
    
    print(f"Testing with audio file: {test_audio}")
    print(f"File size: {test_audio.stat().st_size / 1024:.1f} KB")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Upload file
        url = "https://api.mistral.ai/v1/files"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        data = aiohttp.FormData()
        with open(test_audio, 'rb') as f:
            file_content = f.read()
        data.add_field('file', file_content, filename=test_audio.name, content_type='audio/mpeg')
        data.add_field('purpose', 'audio')
        
        print("\n1. Uploading file...")
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                print(f"Upload failed: {response.status}")
                print(await response.text())
                return
            upload_result = await response.json()
            file_id = upload_result["id"]
            print(f"File uploaded: {file_id}")
        
        # Step 2: Get signed URL
        url = f"https://api.mistral.ai/v1/files/{file_id}/url"
        params = {"expiry": "24"}
        
        print("\n2. Getting signed URL...")
        async with session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                print(f"Failed to get signed URL: {response.status}")
                return
            url_result = await response.json()
            signed_url = url_result["url"]
            print(f"Got signed URL")
        
        # Step 3: Transcribe with verbose_json format (per official docs)
        print("\n3. Transcribing with verbose_json format...")
        transcription_url = "https://api.mistral.ai/v1/audio/transcriptions"
        
        # Use FormData as shown in docs
        data = aiohttp.FormData()
        data.add_field("model", "voxtral-mini-2507")
        data.add_field("file_url", signed_url)
        data.add_field("response_format", "verbose_json")  # This should give us segments
        
        headers = {"x-api-key": api_key}
        
        async with session.post(transcription_url, headers=headers, data=data) as response:
            if response.status != 200:
                print(f"❌ Transcription failed: {response.status}")
                error_text = await response.text()
                print(f"Error: {error_text}")
                return
            
            result = await response.json()
            print(f"✅ Transcription successful!")
            
            # Analyze the response structure
            print(f"\n4. Response Analysis:")
            print(f"   - Keys: {list(result.keys())}")
            print(f"   - Model: {result.get('model', 'N/A')}")
            print(f"   - Language: {result.get('language', 'N/A')}")
            print(f"   - Text length: {len(result.get('text', ''))} chars")
            
            if "segments" in result:
                segments = result["segments"]
                print(f"   - Segments: {len(segments)}")
                if segments:
                    print(f"\n   First 3 segments:")
                    for i, seg in enumerate(segments[:3]):
                        print(f"     [{i}] {seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s")
                        print(f"         Text: {seg.get('text', '')[:100]}...")
                    
                    # Check if we're getting proper timestamps
                    has_timestamps = all('start' in s and 'end' in s for s in segments)
                    print(f"\n   ✅ All segments have timestamps: {has_timestamps}")
            else:
                print("   ❌ No segments in response!")
            
            if "usage" in result:
                usage = result["usage"]
                print(f"\n   Usage stats:")
                print(f"     - Audio seconds: {usage.get('prompt_audio_seconds', 0)}")
                print(f"     - Total tokens: {usage.get('total_tokens', 0)}")
        
        # Step 4: Clean up
        print("\n5. Cleaning up...")
        url = f"https://api.mistral.ai/v1/files/{file_id}"
        async with session.delete(url, headers={"Authorization": f"Bearer {api_key}"}) as response:
            print(f"   File deleted: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_voxtral_transcription())
