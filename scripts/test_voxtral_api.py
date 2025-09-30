#!/usr/bin/env python3
"""
Direct test of Voxtral API to understand actual capabilities.
"""

import os
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_voxtral_api():
    """Test Voxtral API directly to see what it actually returns."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    # Create a small test audio file (or use existing)
    test_audio = Path("test_audio.mp3")
    if not test_audio.exists():
        # Try to find any MP3 file
        for path in Path(".").glob("*.mp3"):
            test_audio = path
            break
        else:
            print("No test audio file found - creating one...")
            import subprocess
            subprocess.run([
                "ffmpeg", "-f", "lavfi", "-i", "sine=frequency=1000:duration=3",
                "-ar", "44100", "test_audio.mp3"
            ], capture_output=True)
            test_audio = Path("test_audio.mp3")
            if not test_audio.exists():
                print("Failed to create test audio")
                return
    
    print(f"Testing with audio file: {test_audio}")
    print(f"File size: {test_audio.stat().st_size / 1024:.1f} KB")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Upload file
        url = "https://api.mistral.ai/v1/files"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        data = aiohttp.FormData()
        # Read file content into memory
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
        
        # Step 3: Test different transcription configurations
        transcription_url = "https://api.mistral.ai/v1/audio/transcriptions"
        
        configs = [
            {
                "name": "Basic",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                }
            },
            {
                "name": "With response_format=json",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                    "response_format": "json",
                }
            },
            {
                "name": "With response_format=verbose_json",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                    "response_format": "verbose_json",
                }
            },
            {
                "name": "With timestamp_granularities",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                    "response_format": "verbose_json",
                    "timestamp_granularities": "segment",
                }
            },
        ]
        
        for config in configs:
            print(f"\n3. Testing: {config['name']}")
            print(f"   Parameters: {json.dumps(config['params'], indent=2)}")
            
            # Use FormData for the request
            data = aiohttp.FormData()
            for key, value in config['params'].items():
                data.add_field(key, value)
            
            headers = {"x-api-key": api_key}
            
            try:
                async with session.post(transcription_url, headers=headers, data=data) as response:
                    if response.status != 200:
                        print(f"   ❌ Failed: {response.status}")
                        error_text = await response.text()
                        print(f"   Error: {error_text[:200]}")
                    else:
                        result = await response.json()
                        print(f"   ✅ Success!")
                        print(f"   Response keys: {list(result.keys())}")
                        
                        # Check for specific features
                        if "text" in result:
                            print(f"   Text length: {len(result['text'])} chars")
                        if "language" in result:
                            print(f"   Language: {result['language']}")
                        if "segments" in result:
                            print(f"   Segments: {len(result['segments'])}")
                            if result['segments']:
                                print(f"   First segment keys: {list(result['segments'][0].keys())}")
                        if "words" in result:
                            print(f"   Words: {len(result['words'])}")
                            if result['words']:
                                print(f"   First word: {result['words'][0]}")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Step 4: Clean up
        print("\n4. Cleaning up...")
        url = f"https://api.mistral.ai/v1/files/{file_id}"
        async with session.delete(url, headers={"Authorization": f"Bearer {api_key}"}) as response:
            print(f"   File deleted: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_voxtral_api())
