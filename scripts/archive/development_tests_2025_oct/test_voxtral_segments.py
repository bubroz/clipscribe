#!/usr/bin/env python3
"""
Test different Voxtral parameter combinations to get segments/timestamps.
"""

import os
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_voxtral_params():
    """Test different parameter combinations."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    # Use the 5-minute speech file
    test_audio = Path("test_speech_5min.mp3")
    if not test_audio.exists():
        print("Test audio not found")
        return
    
    print(f"Testing with: {test_audio} ({test_audio.stat().st_size / 1024:.1f} KB)")
    
    async with aiohttp.ClientSession() as session:
        # Upload file once
        url = "https://api.mistral.ai/v1/files"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        data = aiohttp.FormData()
        with open(test_audio, 'rb') as f:
            file_content = f.read()
        data.add_field('file', file_content, filename=test_audio.name, content_type='audio/mpeg')
        data.add_field('purpose', 'audio')
        
        print("\nUploading file...")
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                print(f"Upload failed: {response.status}")
                return
            upload_result = await response.json()
            file_id = upload_result["id"]
            print(f"File uploaded: {file_id}")
        
        # Get signed URL
        url = f"https://api.mistral.ai/v1/files/{file_id}/url"
        params = {"expiry": "24"}
        
        print("Getting signed URL...")
        async with session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                print(f"Failed to get signed URL: {response.status}")
                return
            url_result = await response.json()
            signed_url = url_result["url"]
        
        # Test different parameter combinations
        test_configs = [
            {
                "name": "With word_timestamps=true",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                    "response_format": "verbose_json",
                    "word_timestamps": "true",  # Try this parameter
                }
            },
            {
                "name": "With timestamps=true",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                    "response_format": "verbose_json",
                    "timestamps": "true",  # Alternative parameter name
                }
            },
            {
                "name": "With include_timestamps=true",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                    "response_format": "verbose_json",
                    "include_timestamps": "true",  # Another possibility
                }
            },
            {
                "name": "With timestamp_granularities=word",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                    "response_format": "verbose_json",
                    "timestamp_granularities": "word",  # Try word level
                }
            },
            {
                "name": "With timestamp_granularities=[word,segment]",
                "params": {
                    "model": "voxtral-mini-2507",
                    "file_url": signed_url,
                    "response_format": "verbose_json",
                    "timestamp_granularities": '["word","segment"]',  # Array format
                }
            },
        ]
        
        transcription_url = "https://api.mistral.ai/v1/audio/transcriptions"
        headers = {"x-api-key": api_key}
        
        for config in test_configs:
            print(f"\n Testing: {config['name']}")
            
            # Use FormData
            data = aiohttp.FormData()
            for key, value in config['params'].items():
                data.add_field(key, value)
            
            try:
                async with session.post(transcription_url, headers=headers, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        # Only show first 200 chars of error
                        print(f"   ❌ Failed ({response.status}): {error_text[:200]}")
                    else:
                        result = await response.json()
                        print(f"   ✅ Success!")
                        print(f"   - Text length: {len(result.get('text', ''))} chars")
                        print(f"   - Language: {result.get('language', 'N/A')}")
                        
                        # Check for different timestamp formats
                        if "segments" in result and result["segments"]:
                            print(f"   - Segments: {len(result['segments'])}")
                            seg = result['segments'][0]
                            print(f"     First segment: {seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s")
                        
                        if "words" in result and result["words"]:
                            print(f"   - Words: {len(result['words'])}")
                            word = result['words'][0]
                            print(f"     First word: '{word.get('word', '')}' at {word.get('start', 0):.2f}s")
                        
                        if "timestamps" in result:
                            print(f"   - Timestamps field present: {type(result['timestamps'])}")
                        
                        # Show any unexpected keys
                        expected_keys = {'model', 'text', 'language', 'segments', 'usage', 'words'}
                        unexpected = set(result.keys()) - expected_keys
                        if unexpected:
                            print(f"   - Unexpected keys: {unexpected}")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Clean up
        print("\nCleaning up...")
        url = f"https://api.mistral.ai/v1/files/{file_id}"
        async with session.delete(url, headers={"Authorization": f"Bearer {api_key}"}) as response:
            print(f"File deleted: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_voxtral_params())
