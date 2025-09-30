#!/usr/bin/env python3
"""
Test uploading file DIRECTLY in transcription request (not via file_url).
This matches some documentation examples.
"""

import os
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_direct_upload():
    """Test uploading file directly in the transcription request."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    # Use a small file for testing
    test_audio = Path("test_audio.mp3")
    if not test_audio.exists():
        print("Creating test audio...")
        import subprocess
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "sine=frequency=1000:duration=10",
            "-ar", "44100", "test_audio.mp3", "-y"
        ], capture_output=True)
    
    print("=" * 60)
    print("TESTING DIRECT FILE UPLOAD TO TRANSCRIPTION ENDPOINT")
    print("=" * 60)
    print(f"\nTest file: {test_audio} ({test_audio.stat().st_size / 1024:.1f} KB)")
    
    async with aiohttp.ClientSession() as session:
        transcription_url = "https://api.mistral.ai/v1/audio/transcriptions"
        
        # Test 1: Direct file upload with multipart/form-data
        print("\n1. Testing direct file upload (multipart/form-data)...")
        
        data = aiohttp.FormData()
        with open(test_audio, 'rb') as f:
            file_content = f.read()
        
        # Add file directly (not file_url)
        data.add_field('file', file_content, filename=test_audio.name, content_type='audio/mpeg')
        data.add_field('model', 'voxtral-mini-2507')
        data.add_field('response_format', 'verbose_json')
        
        # Try different auth headers
        for auth_type in ["Bearer", "x-api-key"]:
            print(f"\n   Testing with {auth_type} auth...")
            
            if auth_type == "Bearer":
                headers = {"Authorization": f"Bearer {api_key}"}
            else:
                headers = {"x-api-key": api_key}
            
            async with session.post(transcription_url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Success with {auth_type}!")
                    print(f"   Response keys: {list(result.keys())}")
                    
                    if "segments" in result:
                        segments = result["segments"]
                        if segments:
                            print(f"   🎯 SEGMENTS FOUND: {len(segments)}")
                            seg = segments[0]
                            print(f"   First segment: {seg}")
                        else:
                            print(f"   ⚠️  Segments empty")
                    
                    # Save response
                    with open(f"direct_upload_{auth_type}.json", "w") as f:
                        json.dump(result, f, indent=2)
                else:
                    error = await response.text()
                    print(f"   ❌ Failed ({response.status}): {error[:100]}...")
        
        # Test 2: Try with base64 encoding
        print("\n2. Testing with base64 encoded audio...")
        import base64
        
        with open(test_audio, 'rb') as f:
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Try JSON body with base64
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        json_data = {
            "model": "voxtral-mini-2507",
            "audio": audio_base64,
            "response_format": "verbose_json"
        }
        
        async with session.post(transcription_url, headers=headers, json=json_data) as response:
            if response.status == 200:
                result = await response.json()
                print(f"   ✅ Success with base64!")
                print(f"   Response keys: {list(result.keys())}")
                
                if "segments" in result and result["segments"]:
                    print(f"   🎯 SEGMENTS FOUND: {len(result['segments'])}")
            else:
                error = await response.text()
                print(f"   ❌ Failed ({response.status}): {error[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_direct_upload())
