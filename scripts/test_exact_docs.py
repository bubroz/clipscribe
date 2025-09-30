#!/usr/bin/env python3
"""
Test EXACTLY as shown in the documentation with timestamp_granularities as array.
"""

import os
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_exact_documentation():
    """Test with the EXACT parameters from the documentation."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    # Use Obama speech or our test speech
    test_audio = Path("test_speech_5min.mp3")
    if not test_audio.exists():
        print(f"Test audio not found: {test_audio}")
        return
    
    print("=" * 60)
    print("TESTING EXACTLY AS DOCUMENTED")
    print("Using timestamp_granularities=['segment'] as ARRAY")
    print("=" * 60)
    print(f"\nTest file: {test_audio} ({test_audio.stat().st_size / 1024:.1f} KB)")
    
    async with aiohttp.ClientSession() as session:
        # Upload file first
        print("\n1. Uploading file...")
        url = "https://api.mistral.ai/v1/files"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        data = aiohttp.FormData()
        with open(test_audio, 'rb') as f:
            file_content = f.read()
        data.add_field('file', file_content, filename=test_audio.name, content_type='audio/mpeg')
        data.add_field('purpose', 'audio')
        
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                print(f"Upload failed: {response.status}")
                return
            upload_result = await response.json()
            file_id = upload_result["id"]
            print(f"   ✅ Uploaded: {file_id}")
        
        # Get signed URL
        print("\n2. Getting signed URL...")
        url = f"https://api.mistral.ai/v1/files/{file_id}/url"
        params = {"expiry": "24"}
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                print(f"Failed to get signed URL: {response.status}")
                return
            url_result = await response.json()
            signed_url = url_result["url"]
            print(f"   ✅ Got signed URL")
        
        # Now test different ways to send timestamp_granularities
        print("\n3. Testing transcription with different parameter formats...")
        
        transcription_url = "https://api.mistral.ai/v1/audio/transcriptions"
        
        test_configs = [
            {
                "name": "Method 1: JSON array in FormData",
                "build_data": lambda: {
                    "model": "voxtral-mini-latest",
                    "file_url": signed_url,
                    "timestamp_granularities": json.dumps(["segment"])  # JSON array as string
                }
            },
            {
                "name": "Method 2: Direct array string",
                "build_data": lambda: {
                    "model": "voxtral-mini-latest",
                    "file_url": signed_url,
                    "timestamp_granularities": '["segment"]'  # Direct array string
                }
            },
            {
                "name": "Method 3: Multiple field values",
                "build_data": lambda: {
                    "model": "voxtral-mini-latest",
                    "file_url": signed_url,
                    "timestamp_granularities[]": "segment"  # PHP-style array notation
                }
            },
            {
                "name": "Method 4: Using voxtral-mini-2507 model",
                "build_data": lambda: {
                    "model": "voxtral-mini-2507",  # Specific model version
                    "file_url": signed_url,
                    "timestamp_granularities": json.dumps(["segment"])
                }
            },
        ]
        
        for config in test_configs:
            print(f"\n   {config['name']}...")
            
            data = aiohttp.FormData()
            params = config['build_data']()
            
            # Add fields to FormData
            for key, value in params.items():
                data.add_field(key, value)
            
            # Use x-api-key header (what's been working)
            headers = {"x-api-key": api_key}
            
            try:
                async with session.post(transcription_url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"      ✅ Success!")
                        
                        # Analyze response
                        if "segments" in result:
                            segments = result["segments"]
                            if segments:
                                print(f"      🎯 SEGMENTS FOUND: {len(segments)} segments!")
                                print(f"      First segment: {segments[0]}")
                                
                                # Save successful response
                                filename = f"success_{config['name'].replace(' ', '_').replace(':', '')}.json"
                                with open(filename, "w") as f:
                                    json.dump(result, f, indent=2)
                                print(f"      Saved to: {filename}")
                                
                                # THIS IS WHAT WE'RE LOOKING FOR!
                                break
                            else:
                                print(f"      ⚠️  Segments field exists but empty")
                        else:
                            print(f"      ❌ No segments field")
                    else:
                        error = await response.text()
                        # Parse error to see what's wrong
                        try:
                            error_json = json.loads(error)
                            if "message" in error_json and "detail" in error_json["message"]:
                                details = error_json["message"]["detail"]
                                if details:
                                    print(f"      ❌ Error: {details[0].get('msg', 'Unknown')}")
                                else:
                                    print(f"      ❌ Error ({response.status})")
                            else:
                                print(f"      ❌ Error ({response.status}): {error[:100]}")
                        except:
                            print(f"      ❌ Error ({response.status}): {error[:100]}")
            except Exception as e:
                print(f"      ❌ Exception: {e}")
        
        # Clean up
        print("\n4. Cleaning up...")
        url = f"https://api.mistral.ai/v1/files/{file_id}"
        async with session.delete(url, headers={"Authorization": f"Bearer {api_key}"}) as response:
            print(f"   File deleted: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_exact_documentation())
