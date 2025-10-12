#!/usr/bin/env python3
"""
Test Voxtral with raw HTTP exactly as shown in documentation.
"""

import os
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_raw_api():
    """Test with raw HTTP matching the curl examples in docs."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY not set")
        return
    
    test_audio = Path("test_speech_5min.mp3")
    if not test_audio.exists():
        print(f"Test audio not found: {test_audio}")
        return
    
    print(f"Testing with: {test_audio} ({test_audio.stat().st_size / 1024:.1f} KB)")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Upload file EXACTLY as in docs
        print("\n1. Uploading file (matching docs example)...")
        
        url = "https://api.mistral.ai/v1/files"
        
        # Try with different auth header formats
        for auth_method in ["Bearer", "x-api-key"]:
            print(f"\n   Trying with {auth_method} auth...")
            
            if auth_method == "Bearer":
                headers = {"Authorization": f"Bearer {api_key}"}
            else:
                headers = {"x-api-key": api_key}
            
            data = aiohttp.FormData()
            with open(test_audio, 'rb') as f:
                file_content = f.read()
            data.add_field('file', file_content, filename=test_audio.name, content_type='audio/mpeg')
            data.add_field('purpose', 'audio')
            
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    upload_result = await response.json()
                    file_id = upload_result["id"]
                    print(f"   ✅ File uploaded: {file_id}")
                    break
                else:
                    print(f"   ❌ Failed with {auth_method}: {response.status}")
                    continue
        else:
            print("Failed to upload file")
            return
        
        # Step 2: Get signed URL
        print("\n2. Getting signed URL...")
        url = f"https://api.mistral.ai/v1/files/{file_id}/url"
        params = {"expiry": "24"}
        
        # Use the auth method that worked
        async with session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                print(f"Failed to get signed URL: {response.status}")
                return
            url_result = await response.json()
            signed_url = url_result["url"]
            print(f"   ✅ Got signed URL")
        
        # Step 3: Test transcription with EXACT parameters from docs
        print("\n3. Testing transcription endpoint...")
        
        transcription_url = "https://api.mistral.ai/v1/audio/transcriptions"
        
        # Test different response formats
        test_formats = [
            "verbose_json",  # Should give segments according to docs
            "json",          # Basic JSON
            "text",          # Plain text
        ]
        
        for format_type in test_formats:
            print(f"\n   Testing response_format='{format_type}'...")
            
            # Build request EXACTLY as shown in curl example
            request_data = {
                "model": "voxtral-mini-2507",
                "file_url": signed_url,
                "response_format": format_type
            }
            
            # Try both JSON body and FormData
            for content_type in ["json", "form"]:
                print(f"      Content-Type: {content_type}")
                
                if content_type == "json":
                    # JSON body (like curl example)
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.post(
                        transcription_url,
                        headers=headers,
                        json=request_data
                    ) as response:
                        await process_response(response, format_type)
                else:
                    # FormData (what we've been using)
                    headers = {"x-api-key": api_key}
                    
                    data = aiohttp.FormData()
                    for key, value in request_data.items():
                        data.add_field(key, value)
                    
                    async with session.post(
                        transcription_url,
                        headers=headers,
                        data=data
                    ) as response:
                        await process_response(response, format_type)
        
        # Clean up
        print("\n4. Cleaning up...")
        url = f"https://api.mistral.ai/v1/files/{file_id}"
        async with session.delete(url, headers={"Authorization": f"Bearer {api_key}"}) as response:
            print(f"   File deleted: {response.status}")

async def process_response(response, format_type):
    """Process and analyze the response."""
    if response.status != 200:
        error = await response.text()
        print(f"         ❌ Failed ({response.status}): {error[:100]}...")
    else:
        if format_type == "text":
            text = await response.text()
            print(f"         ✅ Got text: {len(text)} chars")
        else:
            result = await response.json()
            print(f"         ✅ Success!")
            print(f"         Keys: {list(result.keys())}")
            
            if "segments" in result:
                segments = result["segments"]
                if segments:
                    print(f"         🎯 SEGMENTS FOUND: {len(segments)}")
                    # Show first segment
                    seg = segments[0]
                    print(f"         First segment: {seg}")
                    
                    # Save for analysis
                    with open(f"response_{format_type}.json", "w") as f:
                        json.dump(result, f, indent=2)
                    print(f"         Saved to: response_{format_type}.json")
                else:
                    print(f"         ⚠️  Segments field exists but empty")
            else:
                print(f"         ❌ No segments field")
            
            # Check for undocumented fields
            known_fields = {"model", "text", "language", "segments", "usage"}
            unknown = set(result.keys()) - known_fields
            if unknown:
                print(f"         🔍 Unknown fields: {unknown}")

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING VOXTRAL WITH RAW HTTP")
    print("Matching exact curl examples from documentation")
    print("=" * 60)
    
    asyncio.run(test_raw_api())
